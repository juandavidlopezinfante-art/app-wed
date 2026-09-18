import logging
import os
import sqlite3
import uuid
from typing import Any

import requests
from flask import Flask, jsonify, render_template, request

# ==========================================
# CONFIGURACIÓN DE BASE DE DATOS (SQLite)
# ==========================================
DB_NAME = "ecosistema_privado.db"

def inicializar_base_datos():
    """Crea la base de datos y todas las tablas necesarias si no existen."""
    try:
        conexion = sqlite3.connect(DB_NAME)
        cursor = conexion.cursor()
        
        # Tabla de interacciones del chat
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS interacciones (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                request_id TEXT NOT NULL,
                tool_name TEXT NOT NULL,
                prompt TEXT NOT NULL,
                respuesta TEXT NOT NULL,
                fecha TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Tabla de perfiles de usuario
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS usuarios (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                bio TEXT,
                avatar TEXT,
                fecha_creacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')

        # Tabla de publicaciones y feed (incluyendo contenido de bots)
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS posts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                author TEXT NOT NULL,
                content TEXT NOT NULL,
                media_url TEXT,
                is_bot INTEGER DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')

        # Tabla de foros privados y suscripciones (con el 15% de comisión)
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS foros_privados (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                creator TEXT NOT NULL,
                title TEXT NOT NULL,
                price REAL NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')

        conexion.commit()
        conexion.close()
    except Exception as e:
        print(f"Error al inicializar la base de datos: {e}")

# Inicializamos la BD al arrancar el script
inicializar_base_datos()

def guardar_interaccion(request_id: str, tool_name: str, prompt: str, respuesta: str):
    """Guarda cada prompt y respuesta exitosa de forma privada."""
    try:
        conexion = sqlite3.connect(DB_NAME)
        cursor = conexion.cursor()
        cursor.execute('''
            INSERT INTO interacciones (request_id, tool_name, prompt, respuesta)
            VALUES (?, ?, ?, ?)
        ''', (request_id, tool_name, prompt, respuesta))
        conexion.commit()
        conexion.close()
    except Exception as e:
        print(f"Error al guardar en la base de datos: {e}")


logging.basicConfig(
    level=os.environ.get("LOG_LEVEL", "INFO"),
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)

logger = logging.getLogger("NexusAIProEnterprise")

app = Flask(__name__)

OPENROUTER_URL = os.environ.get(
    "OPENROUTER_URL",
    "https://openrouter.ai/api/v1/chat/completions",
)

# Cambiado a un modelo más estable para evitar errores 502 de saturación gratuita
DEFAULT_MODEL = os.environ.get("OPENROUTER_MODEL", "google/gemini-flash-1.5")

SYSTEM_PROMPT = (
    "Eres el núcleo de inteligencia artificial central de Nexus AI Pro Enterprise. "
    "Responde de forma profesional, estructurada, experta y útil ante solicitudes "
    "sobre redacción, documentos, traducción, código y consultas libres."
)

MAX_PROMPT_LENGTH = int(
    os.environ.get("MAX_PROMPT_LENGTH", "12000")
)

OPENROUTER_TIMEOUT = float(
    os.environ.get("OPENROUTER_TIMEOUT", "35")
)


def error_response(message: str, status_code: int, request_id: str):
    """
    Todas las respuestas de error tienen el mismo formato JSON.
    """
    return (
        jsonify(
            {
                "success": False,
                "error": message,
                "requestId": request_id,
            }
        ),
        status_code,
    )


def call_openrouter(
    messages: list[dict[str, str]],
    request_id: str,
) -> tuple[str | None, tuple[Any, int] | None]:

    api_key = os.environ.get("OPENROUTER_API_KEY")

    if not api_key:
        logger.error(
            "OPENROUTER_API_KEY no está configurada. request_id=%s",
            request_id,
        )
        return None, error_response(
            "El servicio de inteligencia artificial no está configurado en el servidor.",
            503,
            request_id,
        )

    model = os.environ.get(
        "OPENROUTER_MODEL",
        DEFAULT_MODEL,
    )

    app_url = os.environ.get(
        "APP_URL",
        "https://app-wed.onrender.com",
    )

    payload = {
        "model": model,
        "messages": messages,
        "temperature": 0.7,
        "max_tokens": int(
            os.environ.get("OPENROUTER_MAX_TOKENS", "1500")
        ),
    }

    headers = {
        "Authorization": f"Bearer {api_key}",
        "HTTP-Referer": app_url,
        "X-Title": "Nexus AI Pro Enterprise",
        "Content-Type": "application/json",
    }

    try:
        response = requests.post(
            OPENROUTER_URL,
            headers=headers,
            json=payload,
            timeout=OPENROUTER_TIMEOUT,
        )

    except requests.exceptions.Timeout:
        logger.warning(
            "Timeout de OpenRouter. request_id=%s",
            request_id,
        )
        return None, error_response(
            "El proveedor de IA tardó demasiado en responder. Inténtalo de nuevo.",
            504,
            request_id,
        )

    except requests.exceptions.RequestException:
        logger.exception(
            "Error de red con OpenRouter. request_id=%s",
            request_id,
        )
        return None, error_response(
            "No fue posible comunicarse con el proveedor de IA.",
            502,
            request_id,
        )

    if response.status_code != 200:
        logger.error(
            "OpenRouter respondió %s. request_id=%s body=%s",
            response.status_code,
            request_id,
            response.text[:500],
        )

        if response.status_code == 429:
            message = "El proveedor de IA está temporalmente saturado. Espera unos segundos e inténtalo de nuevo."
            status_code = 429
        elif response.status_code in (401, 403):
            message = "El proveedor de IA rechazó la configuración del servidor."
            status_code = 502
        else:
            message = "El proveedor de IA no pudo procesar la solicitud."
            status_code = 502

        return None, error_response(message, status_code, request_id)

    try:
        response_data = response.json()
    except ValueError:
        logger.error(
            "OpenRouter devolvió JSON inválido. request_id=%s",
            request_id,
        )
        return None, error_response(
            "El proveedor de IA devolvió una respuesta inválida.",
            502,
            request_id,
        )

    choices = (
        response_data.get("choices")
        if isinstance(response_data, dict)
        else None
    )

    if (
        not isinstance(choices, list)
        or not choices
        or not isinstance(choices[0], dict)
    ):
        logger.error(
            "OpenRouter devolvió choices vacío. request_id=%s",
            request_id,
        )
        return None, error_response(
            "El proveedor de IA no devolvió contenido.",
            502,
            request_id,
        )

    message = choices[0].get("message")
    content = (
        message.get("content")
        if isinstance(message, dict)
        else None
    )

    if not isinstance(content, str) or not content.strip():
        logger.error(
            "OpenRouter no devolvió contenido. request_id=%s",
            request_id,
        )
        return None, error_response(
            "El proveedor de IA no devolvió contenido.",
            502,
            request_id,
        )

    return content.strip(), None


def get_prompt(
    data: dict[str, Any],
) -> tuple[str | None, str | None]:

    prompt = data.get("prompt") or data.get("message") or ""

    if not isinstance(prompt, str):
        return None, "La solicitud debe contener texto."

    prompt = prompt.strip()

    if not prompt:
        return None, "El mensaje está vacío."

    if len(prompt) > MAX_PROMPT_LENGTH:
        return (
            None,
            f"El mensaje no puede superar {MAX_PROMPT_LENGTH} caracteres.",
        )

    return prompt, None


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/dashboard")
def dashboard():
    return render_template("dashboard.html")


@app.route("/health", methods=["GET"])
def health():
    return jsonify(
        {
            "status": "ok",
            "service": "Nexus AI Pro Enterprise",
            "providerConfigured": bool(
                os.environ.get("OPENROUTER_API_KEY")
            ),
        }
    ), 200


@app.route("/api/chat", methods=["POST"])
def api_chat():
    request_id = uuid.uuid4().hex
    data = request.get_json(silent=True) or {}

    prompt, validation_error = get_prompt(data)
    if validation_error:
        return error_response(validation_error, 400, request_id)

    content, provider_error = call_openrouter(
        [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": prompt},
        ],
        request_id,
    )

    if provider_error:
        return provider_error

    guardar_interaccion(request_id, "Chat General", prompt, content)

    return jsonify(
        {
            "success": True,
            "reply": content,
            "requestId": request_id,
        }
    ), 200


@app.route("/api/generate", methods=["POST"])
def api_generate():
    request_id = uuid.uuid4().hex
    data = request.get_json(silent=True) or {}

    prompt, validation_error = get_prompt(data)
    if validation_error:
        return error_response(validation_error, 400, request_id)

    tool_name = data.get("toolName", "Asistente General")
    if not isinstance(tool_name, str):
        tool_name = "Asistente General"

    tool_name = tool_name.strip()[:120] or "Asistente General"

    content, provider_error = call_openrouter(
        [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": f"Módulo activo: {tool_name}\nSolicitud: {prompt}"},
        ],
        request_id,
    )

    if provider_error:
        return provider_error

    guardar_interaccion(request_id, tool_name, prompt, content)

    return jsonify(
        {
            "success": True,
            "response": content,
            "requestId": request_id,
        }
    ), 200


# ==========================================
# RUTAS PARA BOTS, FOROS E HISTORIAS
# ==========================================

@app.route("/api/bot/generar-feed", methods=["POST"])
def generar_feed_bot():
    """Bot inteligente que crea publicaciones automáticas para mantener vivo el feed."""
    request_id = uuid.uuid4().hex
    prompt_bot = "Genera una publicación corta, atractiva y moderna sobre tecnología, inteligencia artificial o tips de productividad para una red social, incluyendo hashtags."
    
    content, provider_error = call_openrouter(
        [
            {"role": "system", "content": "Eres un bot autónomo creador de contenido viral y tecnológico."},
            {"role": "user", "content": prompt_bot}
        ],
        request_id
    )

    if provider_error:
        return provider_error

    try:
        conexion = sqlite3.connect(DB_NAME)
        cursor = conexion.cursor()
        cursor.execute("INSERT INTO posts (author, content, is_bot) VALUES (?, ?, ?)", ("NexusBot_AI", content, 1))
        conexion.commit()
        conexion.close()
    except Exception as e:
        logger.error(f"Error guardando post de bot: {e}")

    return jsonify({"success": True, "bot_post": content, "requestId": request_id}), 200


@app.route("/api/foros/crear", methods=["POST"])
def crear_foro_privado():
    """Permite a los usuarios crear foros privados definiendo su precio de suscripción."""
    data = request.get_json(silent=True) or {}
    creator = data.get("creator", "").strip()
    title = data.get("title", "").strip()
    try:
        price = float(data.get("price", 0.0))
    except ValueError:
        price = 0.0

    if not creator or not title or price <= 0:
        return jsonify({"success": False, "error": "Datos incompletos o precio inválido."}), 400

    # Cálculo automático de la comisión del 15% para la plataforma
    comision_plataforma = round(price * 0.15, 2)
    ganancia_neta_creador = round(price - comision_plataforma, 2)

    try:
        conexion = sqlite3.connect(DB_NAME)
        cursor = conexion.cursor()
        cursor.execute(
            "INSERT INTO foros_privados (creator, title, price) VALUES (?, ?, ?)",
            (creator, title, price)
        )
        conexion.commit()
        conexion.close()
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

    return jsonify({
        "success": True,
        "message": "Foro privado creado con éxito.",
        "subscriptionDetails": {
            "creatorPrice": price,
            "platformFee15Percent": comision_plataforma,
            "creatorNetEarnings": ganancia_neta_creador
        }
    }), 200


if __name__ == "__main__":
    port = int(os.environ.get("PORT", "5000"))
    app.run(host="0.0.0.0", port=port)

import json
import logging
import os
import re
import sqlite3
import threading
import time
import uuid
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Any

import requests
from dotenv import load_dotenv
from flask import Flask, jsonify, redirect, render_template, request, send_from_directory, session, url_for
from werkzeug.utils import secure_filename

BASE_DIR = Path(__file__).resolve().parent
load_dotenv(BASE_DIR / ".env")

DB_NAME = os.getenv("DB_NAME", "ecosistema_privado.db")

logging.basicConfig(
    level=os.environ.get("LOG_LEVEL", "INFO"),
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("NexusAIProEnterprise")

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "cambia_esta_clave_por_una_mas_segura")

OPENROUTER_URL = os.environ.get(
    "OPENROUTER_URL",
    "https://openrouter.ai/api/v1/chat/completions",
)
DEFAULT_MODEL = os.environ.get("OPENROUTER_MODEL", "openrouter/free")
IMAGE_MODEL = os.getenv("OPENROUTER_IMAGE_MODEL", "google/gemini-2.5-flash-image")
SYSTEM_PROMPT = (
    "Eres el núcleo de inteligencia artificial central de Nexus AI Pro Enterprise. "
    "Responde de forma profesional, estructurada, experta y útil "
    "ante solicitudes sobre redacción, documentos, traducción, código y consultas libres."
)
MAX_PROMPT_LENGTH = int(os.environ.get("MAX_PROMPT_LENGTH", "12000"))
OPENROUTER_TIMEOUT = float(os.environ.get("OPENROUTER_TIMEOUT", "35"))
BOT_INTERVAL_SECONDS = int(os.environ.get("BOT_INTERVAL_SECONDS", str(6 * 60 * 60)))
BOT_CRON_SECRET = os.getenv("BOT_CRON_SECRET", "")
BOT_TRENDS_URL = os.environ.get(
    "BOT_TRENDS_URL",
    "https://trends.google.com/trending/rss?geo=US",
)
UPLOAD_DIR = BASE_DIR / "uploads"
UPLOAD_DIR.mkdir(exist_ok=True)
MAX_UPLOAD_BYTES = int(os.environ.get("MAX_UPLOAD_BYTES", str(25 * 1024 * 1024)))
ALLOWED_UPLOAD_EXTENSIONS = {
    ".jpg", ".jpeg", ".png", ".gif", ".webp", ".mp4", ".webm", ".mov",
    ".mp3", ".wav", ".m4a", ".pdf", ".doc", ".docx", ".xls", ".xlsx",
    ".txt", ".csv",
}


def get_db_connection():
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    return conn


def ensure_user_columns():
    conn = get_db_connection()
    try:
        existing = [row[1] for row in conn.execute("PRAGMA table_info(usuarios)").fetchall()]
        column_defs = {
            "username": "TEXT",
            "email": "TEXT",
            "password": "TEXT",
            "phone": "TEXT",
            "bio": "TEXT",
            "avatar": "TEXT",
            "created_at": "TIMESTAMP DEFAULT CURRENT_TIMESTAMP",
        }
        for column_name, column_def in column_defs.items():
            if column_name not in existing:
                try:
                    conn.execute(f"ALTER TABLE usuarios ADD COLUMN {column_name} {column_def}")
                except sqlite3.OperationalError:
                    pass
        conn.commit()
    finally:
        conn.close()


def ensure_interacciones_columns():
    conn = get_db_connection()
    try:
        existing = {
            row[1] for row in conn.execute("PRAGMA table_info(interacciones)").fetchall()
        }
        required = {
            "request_id": "TEXT NOT NULL DEFAULT ''",
            "tool_name": "TEXT NOT NULL DEFAULT 'Asistente General'",
            "prompt": "TEXT NOT NULL DEFAULT ''",
            "respuesta": "TEXT NOT NULL DEFAULT ''",
        }
        for column_name, column_def in required.items():
            if column_name not in existing:
                conn.execute(
                    f"ALTER TABLE interacciones ADD COLUMN {column_name} {column_def}"
                )
        conn.commit()
    finally:
        conn.close()


def ensure_ai_chat_columns():
    conn = get_db_connection()
    try:
        existing = {row[1] for row in conn.execute("PRAGMA table_info(ai_chat_messages)").fetchall()}
        if "session_token" not in existing:
            conn.execute("ALTER TABLE ai_chat_messages ADD COLUMN session_token TEXT")
        file_columns = {row[1] for row in conn.execute("PRAGMA table_info(ai_files)").fetchall()}
        if "session_token" not in file_columns:
            conn.execute("ALTER TABLE ai_files ADD COLUMN session_token TEXT")
        conn.commit()
    finally:
        conn.close()


def ensure_channel_columns():
    conn = get_db_connection()
    try:
        existing = {row[1] for row in conn.execute("PRAGMA table_info(channels)").fetchall()}
        if "avatar_url" not in existing:
            conn.execute("ALTER TABLE channels ADD COLUMN avatar_url TEXT")
        conn.commit()
    finally:
        conn.close()


def init_db():
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS usuarios (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            email TEXT UNIQUE,
            username TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            phone TEXT,
            bio TEXT,
            avatar TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """
    )
    conn.commit()
    conn.close()
    ensure_interacciones_columns()

    ensure_user_columns()

    conn = get_db_connection()
    cursor = conn.cursor()

    tables = [
        ("posts", """
            CREATE TABLE IF NOT EXISTS posts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                author TEXT NOT NULL,
                content TEXT NOT NULL,
                media_url TEXT,
                is_bot INTEGER DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """),
        ("stories", """
            CREATE TABLE IF NOT EXISTS stories (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                content TEXT,
                media_url TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """),
        ("reels", """
            CREATE TABLE IF NOT EXISTS reels (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                caption TEXT,
                video_url TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """),
        ("follows", """
            CREATE TABLE IF NOT EXISTS follows (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                follower_id INTEGER NOT NULL,
                following_id INTEGER NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """),
        ("messages", """
            CREATE TABLE IF NOT EXISTS messages (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                sender_id INTEGER NOT NULL,
                receiver_id INTEGER NOT NULL,
                message TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """),
        ("channels", """
            CREATE TABLE IF NOT EXISTS channels (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                creator_id INTEGER NOT NULL,
                name TEXT NOT NULL,
                description TEXT,
                avatar_url TEXT,
                is_private INTEGER DEFAULT 0,
                is_adult INTEGER DEFAULT 0,
                monthly_price REAL DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """),
        ("reactions", """
            CREATE TABLE IF NOT EXISTS reactions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                target_type TEXT NOT NULL,
                target_id INTEGER NOT NULL,
                reaction TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """),
        ("interacciones", """
            CREATE TABLE IF NOT EXISTS interacciones (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                request_id TEXT NOT NULL,
                tool_name TEXT NOT NULL,
                prompt TEXT NOT NULL,
                respuesta TEXT NOT NULL,
                fecha TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """),
        ("foros_privados", """
            CREATE TABLE IF NOT EXISTS foros_privados (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                creator TEXT NOT NULL,
                title TEXT NOT NULL,
                price REAL NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """),
        ("ai_interactions", """
            CREATE TABLE IF NOT EXISTS ai_interactions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                request_id TEXT NOT NULL,
                tool_name TEXT NOT NULL,
                prompt TEXT NOT NULL,
                response TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """),
        ("ai_chat_messages", """
            CREATE TABLE IF NOT EXISTS ai_chat_messages (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                session_token TEXT,
                role TEXT NOT NULL,
                content TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """),
        ("ai_files", """
            CREATE TABLE IF NOT EXISTS ai_files (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                session_token TEXT,
                message_id INTEGER,
                original_name TEXT NOT NULL,
                stored_name TEXT NOT NULL UNIQUE,
                mime_type TEXT,
                size_bytes INTEGER NOT NULL DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """),
        ("age_consents", """
            CREATE TABLE IF NOT EXISTS age_consents (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                session_token TEXT NOT NULL UNIQUE,
                confirmed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """),
        ("channel_subscriptions", """
            CREATE TABLE IF NOT EXISTS channel_subscriptions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                channel_id INTEGER NOT NULL,
                subscriber_id INTEGER,
                guest_token TEXT,
                price REAL NOT NULL,
                commission_rate REAL NOT NULL,
                platform_fee REAL NOT NULL,
                creator_earnings REAL NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """),
        ("channel_posts", """
            CREATE TABLE IF NOT EXISTS channel_posts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                channel_id INTEGER NOT NULL,
                author_id INTEGER,
                content TEXT,
                media_url TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """),
    ]

    for _, ddl in tables:
        cursor.execute(ddl)

    conn.commit()
    conn.close()
    ensure_interacciones_columns()
    ensure_ai_chat_columns()
    ensure_channel_columns()


init_db()


def guardar_interaccion(request_id: str, tool_name: str, prompt: str, respuesta: str):
    try:
        conn = get_db_connection()
        conn.execute(
            """
            INSERT INTO interacciones (request_id, tool_name, prompt, respuesta)
            VALUES (?, ?, ?, ?)
            """,
            (request_id, tool_name, prompt, respuesta),
        )
        conn.commit()
        conn.close()
    except Exception as exc:
        logger.exception("Error guardando interacción: %s", exc)


def error_response(message: str, status_code: int, request_id: str):
    return (
        jsonify({"success": False, "error": message, "requestId": request_id}),
        status_code,
    )


def generate_local_fallback_response(tool_name: str, prompt: str) -> str:
    title = (tool_name or "Asistente General").strip() or "Asistente General"
    summary = (prompt or "una idea de contenido").strip()[:200]
    return (
        f"Respuesta local activa para {title}.\n\n"
        f"Solicitud: {summary}\n\n"
        "Idea lista para usar: convierte cada idea en una acción clara, útil y constante "
        "para construir comunidad y generar resultados. #IA #Contenido #Crecimiento"
    )


def fetch_social_trends() -> list[str]:
    try:
        response = requests.get(BOT_TRENDS_URL, timeout=10, headers={"User-Agent": "NexusAIPro/1.0"})
        response.raise_for_status()
        root = ET.fromstring(response.content)
        trends = []
        for item in root.findall(".//item/title"):
            title = (item.text or "").strip()
            if title and title not in trends:
                trends.append(title)
            if len(trends) >= 8:
                break
        return trends
    except (requests.RequestException, ET.ParseError, ValueError) as exc:
        logger.warning("No se pudieron consultar tendencias: %s", exc)
        return []


def get_prompt(data: dict[str, Any]) -> tuple[str | None, str | None]:
    prompt = data.get("prompt") or data.get("message") or ""
    if not isinstance(prompt, str):
        return None, "La solicitud debe contener texto."
    prompt = prompt.strip()
    if not prompt:
        return None, "El mensaje está vacío."
    if len(prompt) > MAX_PROMPT_LENGTH:
        return None, f"El mensaje no puede superar {MAX_PROMPT_LENGTH} caracteres."
    return prompt, None


def is_image_request(prompt: str, tool_name: str = "") -> bool:
    text = f"{tool_name} {prompt}".lower()
    return bool(re.search(r"\b(imagen|imagenes|image|genera.*dibujo|genera.*foto|ilustraci[oó]n|retrato)\b", text))


def extract_image_outputs(response_data: dict[str, Any]) -> list[dict[str, Any]]:
    images = []
    choices = response_data.get("choices") or []
    if not choices or not isinstance(choices[0], dict):
        return images
    message = choices[0].get("message") or {}
    for item in message.get("images") or []:
        if isinstance(item, dict):
            image_url = item.get("image_url") or item.get("url")
            if isinstance(image_url, dict):
                image_url = image_url.get("url")
            if isinstance(image_url, str) and image_url:
                images.append({"url": image_url, "type": "image"})
    content = message.get("content")
    if isinstance(content, list):
        for item in content:
            if not isinstance(item, dict):
                continue
            image_url = item.get("image_url") or item.get("url")
            if isinstance(image_url, dict):
                image_url = image_url.get("url")
            if isinstance(image_url, str) and image_url.startswith(("http://", "https://", "data:image/")):
                images.append({"url": image_url, "type": "image"})
    unique = []
    seen = set()
    for image in images:
        if image["url"] not in seen:
            unique.append(image)
            seen.add(image["url"])
    return unique


def call_openrouter_image(prompt: str, request_id: str):
    api_key = (os.getenv("OPENROUTER_API_KEY") or "").strip()
    if not api_key or api_key.startswith(("PEGA_AQUI_", "tu_")):
        return None, error_response("OPENROUTER_API_KEY no está configurada.", 503, request_id)
    payload = {
        "model": IMAGE_MODEL,
        "messages": [{"role": "user", "content": prompt}],
        "modalities": ["text", "image"],
        "max_tokens": int(os.getenv("OPENROUTER_MAX_TOKENS", "1500")),
    }
    headers = {
        "Authorization": f"Bearer {api_key}",
        "HTTP-Referer": os.getenv("APP_URL", "http://localhost:5000"),
        "X-Title": "Nexus AI Pro Enterprise",
        "Content-Type": "application/json",
    }
    try:
        response = requests.post(OPENROUTER_URL, headers=headers, json=payload, timeout=OPENROUTER_TIMEOUT)
    except requests.RequestException:
        logger.exception("Fallo en generación de imagen. request_id=%s", request_id)
        return None, error_response("No fue posible contactar el generador de imágenes.", 502, request_id)
    if response.status_code != 200:
        logger.error("Generación multimedia fallida: status=%s request_id=%s body=%s", response.status_code, request_id, response.text[:500])
        return None, error_response("El modelo multimedia no pudo generar la imagen. Verifica modelo, permisos y créditos.", 502, request_id)
    try:
        response_data = response.json()
    except ValueError:
        return None, error_response("El proveedor devolvió una respuesta multimedia inválida.", 502, request_id)
    images = extract_image_outputs(response_data)
    if not images:
        return None, error_response("El modelo configurado no devolvió una imagen real.", 502, request_id)
    return {"images": images, "provider": "openrouter", "model": IMAGE_MODEL}, None


def call_openrouter(messages: list[dict[str, str]], request_id: str):
    api_key = (os.getenv("OPENROUTER_API_KEY") or "").strip()
    if (
        not api_key
        or api_key.lower() in {"tu_api_key_de_openrouter", "change_me", "placeholder"}
        or api_key.startswith("PEGA_AQUI_")
    ):
        logger.error("OPENROUTER_API_KEY no configurada o placeholder. request_id=%s", request_id)
        return None, error_response(
            "El servicio de inteligencia artificial no está configurado en el servidor. Configura OPENROUTER_API_KEY en el archivo .env.",
            503,
            request_id,
        )

    app_url = os.environ.get("APP_URL") or "http://localhost:5000"
    payload = {
        "model": os.environ.get("OPENROUTER_MODEL", DEFAULT_MODEL),
        "messages": messages,
        "temperature": 0.7,
        "max_tokens": int(os.environ.get("OPENROUTER_MAX_TOKENS", "1500")),
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
        return None, error_response(
            "El proveedor de IA tardó demasiado en responder. Inténtalo de nuevo.",
            504,
            request_id,
        )
    except requests.exceptions.RequestException as exc:
        logger.exception("Fallo al contactar OpenRouter. request_id=%s", request_id)
        return None, error_response(
            "No fue posible comunicarse con el proveedor de IA.",
            502,
            request_id,
        )

    if response.status_code != 200:
        logger.error(
            "OpenRouter respondió error: status=%s request_id=%s body=%s",
            response.status_code,
            request_id,
            response.text[:500],
        )
        if response.status_code == 429:
            message = "El proveedor de IA está temporalmente saturado. Espera unos segundos e inténtalo de nuevo."
        elif response.status_code in (401, 403):
            message = "La clave de IA es inválida o no tiene permisos."
        else:
            message = "El proveedor de IA no pudo procesar la solicitud."
        return None, error_response(message, 502, request_id)

    try:
        response_data = response.json()
    except ValueError:
        logger.error("Respuesta inválida de OpenRouter. request_id=%s body=%s", request_id, response.text[:500])
        return None, error_response(
            "El proveedor de IA devolvió una respuesta inválida.",
            502,
            request_id,
        )

    choices = response_data.get("choices", [])
    if not choices or not isinstance(choices[0], dict):
        return None, error_response(
            "El proveedor de IA no devolvió contenido.",
            502,
            request_id,
        )

    message_data = choices[0].get("message", {})
    content = message_data.get("content")

    if isinstance(content, list):
        parts = []
        for item in content:
            if isinstance(item, dict):
                text = item.get("text")
                if isinstance(text, str) and text.strip():
                    parts.append(text)
                elif isinstance(item.get("content"), str):
                    parts.append(item["content"])
        content = "\n".join(parts)

    if not isinstance(content, str) or not content.strip():
        return None, error_response(
            "El proveedor de IA no devolvió contenido útil.",
            502,
            request_id,
        )

    return content.strip(), None


@app.route("/")
def index():
    if session.get("user_email"):
        return redirect(url_for("dashboard"))
    return render_template("index.html")


@app.route("/dashboard")
def dashboard():
    if not session.get("user_email"):
        return redirect(url_for("index"))
    return render_template("dashboard.html")


@app.route("/logout")
def logout():
    session.pop("user_id", None)
    session.pop("user_email", None)
    session.pop("user_name", None)
    session.pop("is_guest", None)
    return redirect(url_for("index"))


@app.route("/health", methods=["GET"])
def health():
    api_key = (os.getenv("OPENROUTER_API_KEY") or "").strip()
    provider_configured = bool(api_key) and not api_key.startswith("PEGA_AQUI_")
    return jsonify(
        {
            "status": "ok",
            "service": "Nexus AI Pro Enterprise",
            "providerConfigured": provider_configured,
        }
    ), 200


@app.route("/api/login", methods=["POST"])
def api_login():
    data = request.get_json(silent=True) or {}
    email = (data.get("email") or "").strip()
    username = (data.get("username") or "").strip()
    phone = (data.get("phone") or "").strip()
    password = (data.get("password") or "").strip()

    if not password:
        return jsonify({"success": False, "error": "La contraseña es obligatoria."}), 400

    if not email and not username and not phone:
        return jsonify({"success": False, "error": "Debes enviar email, usuario o celular."}), 400

    conn = get_db_connection()
    user = None

    if email:
        user = conn.execute(
            "SELECT * FROM usuarios WHERE email = ? AND password = ?",
            (email, password),
        ).fetchone()
    elif username:
        user = conn.execute(
            "SELECT * FROM usuarios WHERE username = ? AND password = ?",
            (username, password),
        ).fetchone()
    elif phone:
        user = conn.execute(
            "SELECT * FROM usuarios WHERE phone = ? AND password = ?",
            (phone, password),
        ).fetchone()

    if not user and email:
        generated_username = email.split("@", 1)[0]
        existing = conn.execute(
            "SELECT * FROM usuarios WHERE email = ? OR username = ?",
            (email, generated_username),
        ).fetchone()
        if not existing:
            conn.execute(
                "INSERT INTO usuarios (email, username, password, phone) VALUES (?, ?, ?, ?)",
                (email, generated_username, password, phone or None),
            )
            conn.commit()
            user = conn.execute(
                "SELECT * FROM usuarios WHERE email = ? AND password = ?",
                (email, password),
            ).fetchone()

    conn.close()

    if not user:
        return jsonify({"success": False, "error": "Credenciales inválidas."}), 401

    session["user_id"] = user["id"]
    session["user_email"] = user["email"] or user["username"]
    session["user_name"] = user["username"]
    session.pop("is_guest", None)

    return jsonify(
        {
            "success": True,
            "message": "Sesión iniciada correctamente.",
            "user": {
                "email": user["email"],
                "username": user["username"],
                "phone": user["phone"],
            },
        }
    ), 200


@app.route("/api/register", methods=["POST"])
def api_register():
    data = request.get_json(silent=True) or {}
    email = (data.get("email") or "").strip()
    username = (data.get("username") or "").strip()
    password = (data.get("password") or "").strip()
    phone = (data.get("phone") or "").strip()

    if not email or not username or not password:
        return jsonify({"success": False, "error": "Email, usuario y contraseña son obligatorios."}), 400

    conn = get_db_connection()
    exists = conn.execute(
        "SELECT id FROM usuarios WHERE email = ? OR username = ? OR phone = ?",
        (email, username, phone or ""),
    ).fetchone()

    if exists:
        conn.close()
        return jsonify({"success": False, "error": "Ya existe un usuario con esos datos."}), 409

    conn.execute(
        """
        INSERT INTO usuarios (email, username, password, phone)
        VALUES (?, ?, ?, ?)
        """,
        (email, username, password, phone or None),
    )
    conn.commit()
    user = conn.execute(
        "SELECT * FROM usuarios WHERE email = ? AND password = ?",
        (email, password),
    ).fetchone()
    conn.close()

    if user is not None:
        session["user_id"] = user["id"]
        session["user_email"] = user["email"] or user["username"]
        session["user_name"] = user["username"]
        session.pop("is_guest", None)

    return jsonify({"success": True, "message": "Usuario registrado correctamente."}), 201


@app.route("/api/guest-login", methods=["POST"])
def api_guest_login():
    guest_token = session.get("guest_token") or uuid.uuid4().hex
    session["user_id"] = None
    session["user_email"] = "guest@nexus.local"
    session["user_name"] = "Invitado"
    session["is_guest"] = True
    session["guest_token"] = guest_token
    return jsonify(
        {
            "success": True,
            "message": "Acceso de invitado iniciado.",
            "user": {"username": "Invitado", "guest": True},
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
    save_ai_message("user", prompt)
    save_ai_message("assistant", content)
    return jsonify({"success": True, "reply": content, "requestId": request_id}), 200


def current_session_token():
    if session.get("is_guest"):
        return session.get("guest_token")
    return f"user:{session.get('user_id')}" if session.get("user_id") else None


def has_age_consent():
    token = current_session_token()
    if not token:
        return False
    conn = get_db_connection()
    consent = conn.execute(
        "SELECT 1 FROM age_consents WHERE session_token = ? LIMIT 1", (token,)
    ).fetchone()
    conn.close()
    return consent is not None


@app.route("/api/age/status", methods=["GET"])
def api_age_status():
    return jsonify({"success": True, "confirmed": has_age_consent()}), 200


@app.route("/api/age/verify", methods=["POST"])
def api_age_verify():
    if not session.get("user_email"):
        return jsonify({"success": False, "error": "Debes iniciar sesión o entrar como invitado."}), 401
    data = request.get_json(silent=True) or {}
    if data.get("confirmed") is not True:
        return jsonify({"success": False, "error": "Debes confirmar que tienes 18 años o más."}), 400
    token = current_session_token()
    conn = get_db_connection()
    conn.execute(
        "INSERT OR IGNORE INTO age_consents (user_id, session_token) VALUES (?, ?)",
        (session.get("user_id"), token),
    )
    conn.commit()
    conn.close()
    return jsonify({"success": True, "confirmed": True}), 200


@app.route("/api/generate", methods=["POST"])
def api_generate():
    request_id = uuid.uuid4().hex
    data = request.get_json(silent=True) or {}
    prompt, validation_error = get_prompt(data)
    if validation_error:
        return error_response(validation_error, 400, request_id)

    tool_name = str(data.get("toolName") or "Asistente General").strip() or "Asistente General"

    if is_image_request(prompt, tool_name):
        image_result, image_error = call_openrouter_image(prompt, request_id)
        if image_error:
            return image_error
        save_ai_message("user", prompt)
        save_ai_message("assistant", json.dumps(image_result, ensure_ascii=False))
        return jsonify({
            "success": True,
            "type": "image",
            "response": "Imagen generada por OpenRouter.",
            "images": image_result["images"],
            "provider": image_result["provider"],
            "model": image_result["model"],
            "requestId": request_id,
        }), 200

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
    save_ai_message("user", prompt)
    save_ai_message("assistant", content)
    return jsonify({"success": True, "response": content, "requestId": request_id}), 200


def save_ai_message(role: str, content: str):
    try:
        conn = get_db_connection()
        conn.execute(
            "INSERT INTO ai_chat_messages (user_id, session_token, role, content) "
            "VALUES (?, ?, ?, ?)",
            (session.get("user_id"), session.get("guest_token"), role, content),
        )
        conn.commit()
        conn.close()
    except Exception as exc:
        logger.exception("Error guardando mensaje de IA: %s", exc)


@app.route("/api/ai/history", methods=["GET"])
def api_ai_history():
    conn = get_db_connection()
    messages = conn.execute(
        "SELECT id, role, content, created_at FROM ai_chat_messages "
        "WHERE (user_id IS ? AND session_token IS ?) OR "
        "(user_id = ? AND session_token IS NULL) ORDER BY id DESC LIMIT 100",
        (session.get("user_id"), session.get("guest_token"), session.get("user_id")),
    ).fetchall()
    files = conn.execute(
        "SELECT id, original_name, stored_name, mime_type, size_bytes, created_at "
        "FROM ai_files WHERE (user_id = ? AND session_token IS NULL) OR "
        "(user_id IS NULL AND session_token IS ?) ORDER BY id DESC LIMIT 100",
        (session.get("user_id"), session.get("guest_token")),
    ).fetchall()
    conn.close()
    return jsonify({
        "success": True,
        "messages": [dict(item) for item in reversed(messages)],
        "files": [dict(item) for item in files],
    }), 200


@app.route("/api/ai/files", methods=["POST"])
def api_ai_files():
    if not session.get("user_email"):
        return jsonify({"success": False, "error": "Debes iniciar sesión."}), 401
    uploaded = request.files.get("file")
    if uploaded is None or not uploaded.filename:
        return jsonify({"success": False, "error": "Selecciona un archivo."}), 400
    extension = Path(uploaded.filename).suffix.lower()
    if extension not in ALLOWED_UPLOAD_EXTENSIONS:
        return jsonify({"success": False, "error": "Tipo de archivo no permitido."}), 400
    uploaded.seek(0, os.SEEK_END)
    size_bytes = uploaded.tell()
    uploaded.seek(0)
    if size_bytes > MAX_UPLOAD_BYTES:
        return jsonify({"success": False, "error": "El archivo supera el límite permitido."}), 413
    stored_name = f"{uuid.uuid4().hex}{extension}"
    uploaded.save(UPLOAD_DIR / stored_name)
    conn = get_db_connection()
    conn.execute(
        "INSERT INTO ai_files (user_id, session_token, original_name, stored_name, mime_type, size_bytes) "
        "VALUES (?, ?, ?, ?, ?, ?)",
        (session.get("user_id"), session.get("guest_token"), secure_filename(uploaded.filename), stored_name, uploaded.mimetype, size_bytes),
    )
    conn.commit()
    conn.close()
    return jsonify({"success": True, "file": {
        "name": secure_filename(uploaded.filename),
        "url": url_for("uploaded_file", filename=stored_name),
        "mime_type": uploaded.mimetype,
        "size_bytes": size_bytes,
    }}), 201


@app.route("/uploads/<path:filename>")
def uploaded_file(filename):
    return send_from_directory(UPLOAD_DIR, filename)


@app.route("/api/bot/generar-feed", methods=["POST"])
def generar_feed_bot():
    request_id = uuid.uuid4().hex
    trends = fetch_social_trends()
    trend_context = ", ".join(trends) if trends else "tecnología, inteligencia artificial y productividad"
    prompt_bot = (
        "Crea un lote de contenido para una red social usando estas tendencias actuales como inspiración: "
        f"{trend_context}. "
        "Devuelve únicamente JSON válido con tres claves: post, story y reel. "
        "Cada valor debe ser texto breve listo para publicar; no incluyas markdown ni explicaciones."
    )

    content, provider_error = call_openrouter(
        [
            {"role": "system", "content": "Eres un bot creador de contenido viral y tecnológico."},
            {"role": "user", "content": prompt_bot},
        ],
        request_id,
    )
    fallback = {
        "post": f"Lo que está marcando tendencia hoy: {trend_context}. Convierte la conversación en valor. #IA #Contenido #Crecimiento",
        "story": f"Tendencia del día: {trend_context}. Crea algo útil y compártelo.",
        "reel": f"Cómo convertir {trends[0] if trends else 'una tendencia'} en contenido: claridad, constancia y acción. #Reels #IA",
    }
    batch = fallback
    if not provider_error and content:
        try:
            normalized = content.strip().replace("```json", "").replace("```", "").strip()
            parsed = json.loads(normalized)
            if isinstance(parsed, dict):
                batch = {
                    "post": str(parsed.get("post") or fallback["post"]).strip(),
                    "story": str(parsed.get("story") or fallback["story"]).strip(),
                    "reel": str(parsed.get("reel") or fallback["reel"]).strip(),
                }
        except (TypeError, ValueError, json.JSONDecodeError):
            batch = {"post": content.strip(), "story": fallback["story"], "reel": fallback["reel"]}

    try:
        conn = get_db_connection()
        conn.execute(
            "INSERT INTO posts (author, content, is_bot) VALUES (?, ?, ?)",
            ("NexusBot_AI", batch["post"], 1),
        )
        conn.execute(
            "INSERT INTO stories (user_id, content) VALUES (?, ?)",
            (1, batch["story"]),
        )
        conn.execute(
            "INSERT INTO reels (user_id, caption) VALUES (?, ?)",
            (1, batch["reel"]),
        )
        conn.commit()
        conn.close()
    except Exception as exc:
        logger.exception("Error guardando lote del bot: %s", exc)
        return error_response("No se pudo guardar el lote del bot.", 500, request_id)

    return jsonify({
        "success": True,
        "bot_post": batch["post"],
        "story": batch["story"],
        "reel": batch["reel"],
        "used_fallback": provider_error is not None,
        "requestId": request_id,
    }), 200


@app.route("/api/bot/run-scheduled", methods=["POST"])
def run_scheduled_bot():
    if not BOT_CRON_SECRET or request.headers.get("X-Bot-Secret") != BOT_CRON_SECRET:
        return jsonify({"success": False, "error": "No autorizado."}), 401
    return generar_feed_bot()


@app.route("/api/foros/crear", methods=["POST"])
def crear_foro_privado():
    data = request.get_json(silent=True) or {}
    creator = str(data.get("creator") or "").strip()
    title = str(data.get("title") or "").strip()

    try:
        price = float(data.get("price", 0.0))
    except (TypeError, ValueError):
        price = 0.0

    if not creator or not title or price <= 0:
        return jsonify({"success": False, "error": "Datos incompletos o precio inválido."}), 400

    commission = round(price * 0.15, 2)
    net_income = round(price - commission, 2)

    try:
        conn = get_db_connection()
        conn.execute(
            "INSERT INTO foros_privados (creator, title, price) VALUES (?, ?, ?)",
            (creator, title, price),
        )
        conn.commit()
        conn.close()
    except Exception as exc:
        logger.exception("Error creando foro privado: %s", exc)
        return jsonify({"success": False, "error": "No se pudo crear el foro privado."}), 500

    return jsonify(
        {
            "success": True,
            "message": "Foro privado creado con éxito.",
            "subscriptionDetails": {
                "creatorPrice": price,
                "platformFee15Percent": commission,
                "creatorNetEarnings": net_income,
            },
        }
    ), 200


@app.route("/api/feed", methods=["GET"])
def api_feed():
    conn = get_db_connection()
    posts = conn.execute("SELECT * FROM posts ORDER BY created_at DESC LIMIT 20").fetchall()
    conn.close()

    return jsonify(
        {
            "success": True,
            "posts": [
                {
                    "id": p["id"],
                    "author": p["author"],
                    "content": p["content"],
                    "media_url": p["media_url"],
                    "is_bot": bool(p["is_bot"]),
                    "created_at": p["created_at"],
                }
                for p in posts
            ],
        }
    )


@app.route("/api/reels", methods=["GET"])
def api_reels():
    conn = get_db_connection()
    reels = conn.execute(
        "SELECT reels.*, COALESCE(usuarios.username, 'Creador') AS author "
        "FROM reels LEFT JOIN usuarios ON usuarios.id = reels.user_id "
        "ORDER BY reels.created_at DESC LIMIT 30"
    ).fetchall()
    conn.close()
    return jsonify({"success": True, "reels": [dict(item) for item in reels]}), 200


@app.route("/api/stories", methods=["GET"])
def api_stories():
    conn = get_db_connection()
    stories = conn.execute(
        "SELECT stories.*, COALESCE(usuarios.username, 'Comunidad') AS author "
        "FROM stories LEFT JOIN usuarios ON usuarios.id = stories.user_id "
        "ORDER BY stories.created_at DESC LIMIT 30"
    ).fetchall()
    conn.close()
    return jsonify({"success": True, "stories": [dict(item) for item in stories]}), 200


@app.route("/api/channels", methods=["GET"])
def api_channels():
    requested_type = request.args.get("type", "all")
    conn = get_db_connection()
    base_query = (
        "SELECT channels.*, COALESCE(usuarios.username, 'Creador') AS creator_name "
        "FROM channels LEFT JOIN usuarios ON usuarios.id = channels.creator_id"
    )
    params = []
    if requested_type == "public":
        base_query += " WHERE channels.is_private = 0 AND channels.is_adult = 0"
    elif requested_type == "private":
        base_query += " WHERE channels.is_private = 1 AND channels.is_adult = 0"
    elif requested_type == "adult":
        base_query += " WHERE channels.is_adult = 1"
    base_query += " ORDER BY channels.created_at DESC LIMIT 50"
    channels = conn.execute(base_query, params).fetchall()
    visible = []
    user_id = session.get("user_id")
    guest_token = session.get("guest_token")
    for channel in channels:
        subscribed = conn.execute(
            "SELECT 1 FROM channel_subscriptions WHERE channel_id = ? "
            "AND ((subscriber_id IS NOT NULL AND subscriber_id = ?) OR "
            "(guest_token IS NOT NULL AND guest_token = ?)) LIMIT 1",
            (channel["id"], user_id, guest_token),
        ).fetchone()
        item = dict(channel)
        item["subscribed"] = subscribed is not None
        if requested_type in {"private", "adult"} and not item["subscribed"]:
            item["locked"] = True
        visible.append(item)
    conn.close()
    return jsonify({"success": True, "channels": visible, "type": requested_type}), 200


@app.route("/api/videos", methods=["GET"])
def api_videos():
    conn = get_db_connection()
    videos = conn.execute(
        "SELECT id, author, content, media_url, created_at FROM posts "
        "WHERE lower(media_url) LIKE '%.mp4' OR lower(media_url) LIKE '%.webm' "
        "OR lower(media_url) LIKE '%.mov' ORDER BY created_at DESC LIMIT 50"
    ).fetchall()
    conn.close()
    return jsonify({"success": True, "videos": [dict(item) for item in videos]}), 200


@app.route("/api/channel-posts", methods=["GET"])
def api_channel_posts():
    requested_type = request.args.get("type", "public")
    if requested_type == "adult":
        age_error = require_adult_access()
        if age_error:
            return age_error
    conn = get_db_connection()
    conditions = ["channels.is_private = 0", "channels.is_adult = 0"]
    if requested_type == "private":
        conditions = ["channels.is_private = 1", "channels.is_adult = 0"]
    elif requested_type == "adult":
        conditions = ["channels.is_adult = 1"]
    user_id = session.get("user_id")
    guest_token = session.get("guest_token")
    query = (
        "SELECT channel_posts.*, channels.name AS channel_name FROM channel_posts "
        "JOIN channels ON channels.id = channel_posts.channel_id "
        f"WHERE {' AND '.join(conditions)}"
    )
    params = []
    if requested_type in {"private", "adult"}:
        query += (
            " AND EXISTS (SELECT 1 FROM channel_subscriptions "
            "WHERE channel_subscriptions.channel_id = channels.id AND "
            "((subscriber_id IS NOT NULL AND subscriber_id = ?) OR "
            "(guest_token IS NOT NULL AND guest_token = ?)))"
        )
        params.extend([user_id, guest_token])
    query += " ORDER BY channel_posts.created_at DESC LIMIT 100"
    rows = conn.execute(query, params).fetchall()
    conn.close()
    return jsonify({"success": True, "posts": [dict(row) for row in rows]}), 200


def require_adult_access():
    if not has_age_consent():
        return jsonify({
            "success": False,
            "error": "Confirma que tienes 18 años o más para acceder a esta zona.",
            "requiresAgeConfirmation": True,
        }), 403
    return None


def require_login_json():
    if not session.get("user_email"):
        return jsonify({"success": False, "error": "Debes iniciar sesión para continuar."}), 401
    return None


@app.route("/api/posts/create", methods=["POST"])
def api_posts_create():
    login_error = require_login_json()
    if login_error:
        return login_error

    if request.files:
        content = (request.form.get("content") or request.form.get("text") or "").strip()
        uploaded = request.files.get("file")
        media_url = ""
        if uploaded is not None and uploaded.filename:
            extension = Path(uploaded.filename).suffix.lower()
            if extension not in ALLOWED_UPLOAD_EXTENSIONS:
                return jsonify({"success": False, "error": "Tipo de archivo no permitido."}), 400
            uploaded.seek(0, os.SEEK_END)
            size_bytes = uploaded.tell()
            uploaded.seek(0)
            if size_bytes > MAX_UPLOAD_BYTES:
                return jsonify({"success": False, "error": "El archivo supera el límite permitido."}), 413
            stored_name = f"{uuid.uuid4().hex}{extension}"
            uploaded.save(UPLOAD_DIR / stored_name)
            media_url = url_for("uploaded_file", filename=stored_name)
        elif not content:
            return jsonify({"success": False, "error": "Selecciona un archivo o escribe algo."}), 400
    else:
        data = request.get_json(silent=True) or {}
        content = (data.get("content") or data.get("text") or "").strip()
        media_url = (data.get("media_url") or "").strip()

    if not content and not media_url:
        return jsonify({"success": False, "error": "Escribe algo o agrega contenido multimedia."}), 400

    author = session.get("user_name") or session.get("user_email") or "usuario"
    conn = get_db_connection()
    conn.execute(
        "INSERT INTO posts (author, content, media_url, is_bot) VALUES (?, ?, ?, ?)",
        (author, content or "", media_url or None, 0),
    )
    conn.commit()
    conn.close()

    return jsonify({"success": True, "message": "Publicación creada correctamente.", "media_url": media_url or None}), 201


@app.route("/api/stories/create", methods=["POST"])
def api_stories_create():
    login_error = require_login_json()
    if login_error:
        return login_error

    data = request.get_json(silent=True) or {}
    content = (data.get("content") or "").strip()
    media_url = (data.get("media_url") or "").strip()

    if not content and not media_url:
        return jsonify({"success": False, "error": "La historia no puede estar vacía."}), 400

    user_id = session.get("user_id")
    if not user_id:
        user_id = 1

    conn = get_db_connection()
    conn.execute(
        "INSERT INTO stories (user_id, content, media_url) VALUES (?, ?, ?)",
        (user_id, content or "", media_url or None),
    )
    conn.commit()
    conn.close()

    return jsonify({"success": True, "message": "Historia creada correctamente."}), 201


@app.route("/api/reels/create", methods=["POST"])
def api_reels_create():
    login_error = require_login_json()
    if login_error:
        return login_error

    data = request.get_json(silent=True) or {}
    caption = (data.get("caption") or "").strip()
    video_url = (data.get("video_url") or "").strip()

    if not caption and not video_url:
        return jsonify({"success": False, "error": "El reel necesita caption o video."}), 400

    user_id = session.get("user_id")
    if not user_id:
        user_id = 1

    conn = get_db_connection()
    conn.execute(
        "INSERT INTO reels (user_id, caption, video_url) VALUES (?, ?, ?)",
        (user_id, caption or "", video_url or None),
    )
    conn.commit()
    conn.close()

    return jsonify({"success": True, "message": "Reel creado correctamente."}), 201


@app.route("/api/follow", methods=["POST"])
def api_follow():
    login_error = require_login_json()
    if login_error:
        return login_error

    data = request.get_json(silent=True) or {}
    following_id = data.get("following_id")
    if following_id is None:
        return jsonify({"success": False, "error": "Falta el usuario a seguir."}), 400

    follower_id = session.get("user_id")
    if not follower_id:
        follower_id = 1

    conn = get_db_connection()
    conn.execute(
        "INSERT INTO follows (follower_id, following_id) VALUES (?, ?)",
        (follower_id, int(following_id)),
    )
    conn.commit()
    conn.close()

    return jsonify({"success": True, "message": "Seguimiento realizado."}), 201


@app.route("/api/messages/send", methods=["POST"])
def api_messages_send():
    login_error = require_login_json()
    if login_error:
        return login_error

    data = request.get_json(silent=True) or {}
    receiver_id = data.get("receiver_id")
    message = (data.get("message") or "").strip()

    if receiver_id is None or not message:
        return jsonify({"success": False, "error": "Faltan datos del mensaje."}), 400

    sender_id = session.get("user_id")
    if not sender_id:
        sender_id = 1

    conn = get_db_connection()
    conn.execute(
        "INSERT INTO messages (sender_id, receiver_id, message) VALUES (?, ?, ?)",
        (sender_id, int(receiver_id), message),
    )
    conn.commit()
    conn.close()

    return jsonify({"success": True, "message": "Mensaje enviado."}), 201


@app.route("/api/channels/create", methods=["POST"])
def api_channels_create():
    login_error = require_login_json()
    if login_error:
        return login_error

    if not session.get("user_id"):
        return jsonify({"success": False, "error": "Solo usuarios registrados pueden crear canales."}), 403

    data = request.get_json(silent=True) or {}
    name = (data.get("name") or "").strip()
    description = (data.get("description") or "").strip()
    avatar_url = (data.get("avatar_url") or "").strip()
    is_private = bool(data.get("is_private"))
    is_adult = bool(data.get("is_adult"))
    try:
        monthly_price = round(float(data.get("monthly_price", 0)), 2)
    except (TypeError, ValueError):
        monthly_price = 0
    if not name or monthly_price < 0:
        return jsonify({"success": False, "error": "Nombre o precio inválido."}), 400
    if is_adult:
        age_error = require_adult_access()
        if age_error:
            return age_error
        is_private = True
    if is_private and monthly_price <= 0:
        return jsonify({"success": False, "error": "Un canal privado debe tener un precio mensual mayor que cero."}), 400

    creator_id = session.get("user_id")

    conn = get_db_connection()
    conn.execute(
        "INSERT INTO channels (creator_id, name, description, avatar_url, is_private, is_adult, monthly_price) "
        "VALUES (?, ?, ?, ?, ?, ?, ?)",
        (creator_id, name, description or "", avatar_url or None, int(is_private), int(is_adult), monthly_price),
    )
    conn.commit()
    conn.close()

    return jsonify({
        "success": True,
        "message": "Canal creado correctamente.",
        "channel": {
            "name": name,
            "avatar_url": avatar_url or None,
            "is_private": is_private,
            "is_adult": is_adult,
            "monthly_price": monthly_price,
            "commission_rate": 0.18 if is_adult else (0.15 if is_private else 0),
        },
    }), 201


@app.route("/api/channels/<int:channel_id>/subscribe", methods=["POST"])
def api_channel_subscribe(channel_id):
    if not session.get("user_email"):
        return jsonify({"success": False, "error": "Debes iniciar sesión para suscribirte."}), 401
    conn = get_db_connection()
    channel = conn.execute("SELECT * FROM channels WHERE id = ?", (channel_id,)).fetchone()
    if channel is None:
        conn.close()
        return jsonify({"success": False, "error": "Canal no encontrado."}), 404
    if channel["is_adult"]:
        age_error = require_adult_access()
        if age_error:
            conn.close()
            return age_error
    price = float(channel["monthly_price"] or 0)
    if price <= 0:
        conn.close()
        return jsonify({"success": True, "message": "El canal público no requiere suscripción."}), 200
    rate = 0.18 if channel["is_adult"] else 0.15
    fee = round(price * rate, 2)
    earnings = round(price - fee, 2)
    conn.execute(
        "INSERT INTO channel_subscriptions "
        "(channel_id, subscriber_id, guest_token, price, commission_rate, platform_fee, creator_earnings) "
        "VALUES (?, ?, ?, ?, ?, ?, ?)",
        (channel_id, session.get("user_id"), session.get("guest_token"), price, rate, fee, earnings),
    )
    conn.commit()
    conn.close()
    return jsonify({
        "success": True,
        "message": "Suscripción registrada.",
        "subscription": {"price": price, "platform_fee": fee, "creator_earnings": earnings},
    }), 201


@app.route("/api/reaction", methods=["POST"])
def api_reaction():
    login_error = require_login_json()
    if login_error:
        return login_error

    data = request.get_json(silent=True) or {}
    target_type = (data.get("target_type") or "").strip()
    target_id = data.get("target_id")
    reaction = (data.get("reaction") or "").strip()

    if not target_type or target_id is None or not reaction:
        return jsonify({"success": False, "error": "Datos incompletos para la reacción."}), 400

    user_id = session.get("user_id")
    if not user_id:
        user_id = 1

    conn = get_db_connection()
    conn.execute(
        "INSERT INTO reactions (user_id, target_type, target_id, reaction) VALUES (?, ?, ?, ?)",
        (user_id, target_type, int(target_id), reaction),
    )
    conn.commit()
    conn.close()

    return jsonify({"success": True, "message": "Reacción registrada."}), 201


def start_bot_scheduler():
    if os.getenv("BOT_AUTOSTART", "1").lower() not in {"1", "true", "yes"}:
        return
    if getattr(app, "_bot_scheduler_started", False):
        return
    app._bot_scheduler_started = True

    def scheduler():
        while True:
            time.sleep(BOT_INTERVAL_SECONDS)
            try:
                with app.app_context():
                    generar_feed_bot()
                logger.info("Lote automático de contenido generado correctamente.")
            except Exception:
                logger.exception("Error en el programador automático de contenido.")

    threading.Thread(target=scheduler, name="nexus-content-bot", daemon=True).start()


start_bot_scheduler()


if __name__ == "__main__":
    port = int(os.environ.get("PORT", "5000"))
    app.run(host="0.0.0.0", port=port, debug=True)

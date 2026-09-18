import logging
import os
import sqlite3
import uuid
from pathlib import Path
from typing import Any

import requests
from dotenv import load_dotenv
from flask import Flask, jsonify, redirect, render_template, request, session, url_for

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
SYSTEM_PROMPT = (
    "Eres el núcleo de inteligencia artificial central de Nexus AI Pro Enterprise. "
    "Responde de forma profesional, estructurada, experta y útil "
    "ante solicitudes sobre redacción, documentos, traducción, código y consultas libres."
)
MAX_PROMPT_LENGTH = int(os.environ.get("MAX_PROMPT_LENGTH", "12000"))
OPENROUTER_TIMEOUT = float(os.environ.get("OPENROUTER_TIMEOUT", "35"))


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
    ]

    for _, ddl in tables:
        cursor.execute(ddl)

    conn.commit()
    conn.close()
    ensure_interacciones_columns()


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
    session["user_id"] = None
    session["user_email"] = "guest@nexus.local"
    session["user_name"] = "Invitado"
    session["is_guest"] = True
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
        content = generate_local_fallback_response("Chat General", prompt)

    guardar_interaccion(request_id, "Chat General", prompt, content)
    return jsonify({"success": True, "reply": content, "requestId": request_id}), 200


@app.route("/api/generate", methods=["POST"])
def api_generate():
    request_id = uuid.uuid4().hex
    data = request.get_json(silent=True) or {}
    prompt, validation_error = get_prompt(data)
    if validation_error:
        return error_response(validation_error, 400, request_id)

    tool_name = str(data.get("toolName") or "Asistente General").strip() or "Asistente General"

    content, provider_error = call_openrouter(
        [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": f"Módulo activo: {tool_name}\nSolicitud: {prompt}"},
        ],
        request_id,
    )
    if provider_error:
        content = generate_local_fallback_response(tool_name, prompt)

    guardar_interaccion(request_id, tool_name, prompt, content)
    return jsonify({"success": True, "response": content, "requestId": request_id}), 200


@app.route("/api/bot/generar-feed", methods=["POST"])
def generar_feed_bot():
    request_id = uuid.uuid4().hex
    prompt_bot = (
        "Genera una publicación corta, moderna y atractiva sobre tecnología, "
        "inteligencia artificial o productividad para una red social, "
        "incluyendo hashtags relevantes."
    )

    content, provider_error = call_openrouter(
        [
            {"role": "system", "content": "Eres un bot creador de contenido viral y tecnológico."},
            {"role": "user", "content": prompt_bot},
        ],
        request_id,
    )
    if provider_error:
        content = generate_local_fallback_response("Bot Generador de Feed", prompt_bot)

    try:
        conn = get_db_connection()
        conn.execute(
            "INSERT INTO posts (author, content, is_bot) VALUES (?, ?, ?)",
            ("NexusBot_AI", content, 1),
        )
        conn.commit()
        conn.close()
    except Exception as exc:
        logger.exception("Error guardando post del bot: %s", exc)
        return error_response("No se pudo guardar el post del bot.", 500, request_id)

    return jsonify({"success": True, "bot_post": content, "requestId": request_id}), 200


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


def require_login_json():
    if not session.get("user_email"):
        return jsonify({"success": False, "error": "Debes iniciar sesión para continuar."}), 401
    return None


@app.route("/api/posts/create", methods=["POST"])
def api_posts_create():
    login_error = require_login_json()
    if login_error:
        return login_error

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

    return jsonify({"success": True, "message": "Publicación creada correctamente."}), 201


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

    data = request.get_json(silent=True) or {}
    name = (data.get("name") or "").strip()
    description = (data.get("description") or "").strip()
    if not name:
        return jsonify({"success": False, "error": "El nombre del canal es obligatorio."}), 400

    creator_id = session.get("user_id")
    if not creator_id:
        creator_id = 1

    conn = get_db_connection()
    conn.execute(
        "INSERT INTO channels (creator_id, name, description) VALUES (?, ?, ?)",
        (creator_id, name, description or ""),
    )
    conn.commit()
    conn.close()

    return jsonify({"success": True, "message": "Canal creado correctamente."}), 201


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


if __name__ == "__main__":
    port = int(os.environ.get("PORT", "5000"))
    app.run(host="0.0.0.0", port=port, debug=True)

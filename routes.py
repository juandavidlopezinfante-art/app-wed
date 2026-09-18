import uuid
from flask import Blueprint, jsonify, request, session
from config import Config
from database import get_connection
from services.ai_service import call_openrouter

api = Blueprint("api", __name__)

def get_prompt(data):
    prompt = data.get("prompt") or data.get("message") or ""
    if not isinstance(prompt, str):
        return None, "La solicitud debe contener texto."
    prompt = prompt.strip()
    if not prompt:
        return None, "El mensaje está vacío."
    if len(prompt) > Config.MAX_PROMPT_LENGTH:
        return None, f"El mensaje no puede superar {Config.MAX_PROMPT_LENGTH} caracteres."
    return prompt, None

@api.route("/health", methods=["GET"])
def health():
    return jsonify({
        "status": "ok",
        "service": "Nexus AI Pro Enterprise",
        "providerConfigured": bool(Config.OPENROUTER_API_KEY),
    }), 200

@api.route("/api/login", methods=["POST"])
def login():
    data = request.get_json(silent=True) or {}
    email = (data.get("email") or "").strip()
    password = (data.get("password") or "").strip()

    if not email or not password:
        return jsonify({"success": False, "error": "Correo y contraseña obligatorios."}), 400

    conn = get_connection()
    user = conn.execute(
        "SELECT * FROM users WHERE email = ? AND password = ?",
        (email, password),
    ).fetchone()
    conn.close()

    if not user:
        return jsonify({"success": False, "error": "Credenciales inválidas."}), 401

    session["user_id"] = user["id"]
    session["username"] = user["username"]

    return jsonify({
        "success": True,
        "message": "Inicio de sesión correcto.",
        "user": {
            "id": user["id"],
            "email": user["email"],
            "username": user["username"],
        }
    }), 200

@api.route("/api/register", methods=["POST"])
def register():
    data = request.get_json(silent=True) or {}
    email = (data.get("email") or "").strip()
    username = (data.get("username") or "").strip()
    password = (data.get("password") or "").strip()

    if not email or not username or not password:
        return jsonify({"success": False, "error": "Faltan datos obligatorios."}), 400

    conn = get_connection()
    existing = conn.execute(
        "SELECT id FROM users WHERE email = ? OR username = ?",
        (email, username),
    ).fetchone()

    if existing:
        conn.close()
        return jsonify({"success": False, "error": "Correo o usuario ya registrados."}), 409

    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO users (email, username, password) VALUES (?, ?, ?)",
        (email, username, password),
    )
    conn.commit()
    conn.close()

    return jsonify({"success": True, "message": "Usuario registrado exitosamente."}), 201

@api.route("/api/chat", methods=["POST"])
def chat():
    request_id = uuid.uuid4().hex
    data = request.get_json(silent=True) or {}
    prompt, validation_error = get_prompt(data)
    if validation_error:
        return jsonify({"success": False, "error": validation_error, "requestId": request_id}), 400

    content, provider_error = call_openrouter(
        [
            {"role": "system", "content": "Eres un asistente IA útil y profesional."},
            {"role": "user", "content": prompt},
        ],
        request_id,
    )
    if provider_error:
        return provider_error

    conn = get_connection()
    conn.execute(
        "INSERT INTO ai_interactions (request_id, tool_name, prompt, response) VALUES (?, ?, ?, ?)",
        (request_id, "Chat General", prompt, content),
    )
    conn.commit()
    conn.close()

    return jsonify({"success": True, "reply": content, "requestId": request_id}), 200

@api.route("/api/generate", methods=["POST"])
def generate():
    request_id = uuid.uuid4().hex
    data = request.get_json(silent=True) or {}
    prompt, validation_error = get_prompt(data)
    if validation_error:
        return jsonify({"success": False, "error": validation_error, "requestId": request_id}), 400

    tool_name = (data.get("toolName") or "Asistente General").strip() or "Asistente General"

    content, provider_error = call_openrouter(
        [
            {"role": "system", "content": "Eres el núcleo de IA del sistema."},
            {"role": "user", "content": f"Modulo: {tool_name}\nPedido: {prompt}"},
        ],
        request_id,
    )
    if provider_error:
        return provider_error

    conn = get_connection()
    conn.execute(
        "INSERT INTO ai_interactions (request_id, tool_name, prompt, response) VALUES (?, ?, ?, ?)",
        (request_id, tool_name, prompt, content),
    )
    conn.commit()
    conn.close()

    return jsonify({"success": True, "response": content, "requestId": request_id}), 200

def register_routes(app):
    app.register_blueprint(api)

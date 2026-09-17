import logging
import os
import uuid
from typing import Any

import requests
from flask import Flask, jsonify, render_template, request


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

DEFAULT_MODEL = "mistralai/mistral-7b-instruct:free"

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
            message = (
                "El proveedor de IA está temporalmente saturado. "
                "Espera unos segundos e inténtalo de nuevo."
            )
            status_code = 429

        elif response.status_code in (401, 403):
            message = (
                "El proveedor de IA rechazó la configuración del servidor."
            )
            status_code = 502

        else:
            message = (
                "El proveedor de IA no pudo procesar la solicitud."
            )
            status_code = 502

        return None, error_response(
            message,
            status_code,
            request_id,
        )

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
        return error_response(
            validation_error,
            400,
            request_id,
        )

    content, provider_error = call_openrouter(
        [
            {
                "role": "system",
                "content": SYSTEM_PROMPT,
            },
            {
                "role": "user",
                "content": prompt,
            },
        ],
        request_id,
    )

    if provider_error:
        return provider_error

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
        return error_response(
            validation_error,
            400,
            request_id,
        )

    tool_name = data.get(
        "toolName",
        "Asistente General",
    )

    if not isinstance(tool_name, str):
        tool_name = "Asistente General"

    tool_name = tool_name.strip()[:120]

    if not tool_name:
        tool_name = "Asistente General"

    content, provider_error = call_openrouter(
        [
            {
                "role": "system",
                "content": SYSTEM_PROMPT,
            },
            {
                "role": "user",
                "content": (
                    f"Módulo activo: {tool_name}\n"
                    f"Solicitud: {prompt}"
                ),
            },
        ],
        request_id,
    )

    if provider_error:
        return provider_error

    return jsonify(
        {
            "success": True,
            "response": content,
            "requestId": request_id,
        }
    ), 200


if __name__ == "__main__":
    port = int(
        os.environ.get("PORT", "5000")
    )

    app.run(
        host="0.0.0.0",
        port=port,
    )
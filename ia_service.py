import logging
import requests
from flask import jsonify
from config import Config

logger = logging.getLogger(__name__)

def ai_error(message, status_code, request_id):
    return jsonify({
        "success": False,
        "error": message,
        "requestId": request_id
    }), status_code

def call_openrouter(messages, request_id):
    api_key = Config.OPENROUTER_API_KEY

    if not api_key or api_key.lower() in {"tu_api_key_de_openrouter", "change_me", "placeholder"}:
        logger.error("OPENROUTER_API_KEY no configurada. request_id=%s", request_id)
        return None, ai_error(
            "El servicio de IA no está configurado en el servidor.",
            503,
            request_id,
        )

    payload = {
        "model": Config.OPENROUTER_MODEL,
        "messages": messages,
        "temperature": 0.7,
        "max_tokens": Config.OPENROUTER_MAX_TOKENS,
    }

    headers = {
        "Authorization": f"Bearer {api_key}",
        "HTTP-Referer": Config.APP_URL,
        "X-Title": "Nexus AI Pro Enterprise",
        "Content-Type": "application/json",
    }

    try:
        response = requests.post(
            Config.OPENROUTER_URL,
            headers=headers,
            json=payload,
            timeout=Config.OPENROUTER_TIMEOUT,
        )
    except requests.exceptions.Timeout:
        return None, ai_error(
            "El proveedor de IA tardó demasiado en responder.",
            504,
            request_id,
        )
    except requests.exceptions.RequestException as exc:
        logger.error("Error de conexión con OpenRouter. request_id=%s error=%s", request_id, exc)
        return None, ai_error(
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
            message = "El proveedor de IA está temporalmente saturado."
        elif response.status_code in (401, 403):
            message = "La API key de IA es inválida o no tiene permisos."
        else:
            message = "El proveedor de IA no pudo procesar la solicitud."
        return None, ai_error(message, 502, request_id)

    try:
        data = response.json()
    except ValueError:
        logger.error("Respuesta no JSON de OpenRouter. request_id=%s", request_id)
        return None, ai_error("La respuesta del proveedor de IA no es válida.", 502, request_id)

    choices = data.get("choices", [])
    if not choices or not isinstance(choices[0], dict):
        return None, ai_error("OpenRouter no devolvió contenido válido.", 502, request_id)

    message = choices[0].get("message", {})
    content = message.get("content")

    if isinstance(content, list):
        parts = []
        for item in content:
            if isinstance(item, dict):
                text = item.get("text")
                if isinstance(text, str):
                    parts.append(text)
        content = "\n".join(parts)

    if not isinstance(content, str) or not content.strip():
        return None, ai_error("OpenRouter no devolvió texto usable.", 502, request_id)

    return content.strip(), None

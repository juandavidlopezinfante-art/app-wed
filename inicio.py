import os
import logging
import requests
from flask import Flask, request, jsonify, render_template

# Configuración de logs para monitorear el rendimiento en tiempo real
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
logger = logging.getLogger("NexusAIProEnterprise")

app = Flask(__name__)

# Llave de API y Endpoint de OpenRouter
OPENROUTER_API_KEY = os.environ.get("OPENROUTER_API_KEY")
OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/health', methods=['GET'])
def health():
    return jsonify({"status": "ok", "service": "Nexus AI Pro Enterprise Running"}), 200

# Ruta principal para procesar los mensajes del chat y las herramientas de IA
@app.route('/api/chat', methods=['POST'])
def api_chat():
    try:
        data = request.get_json(silent=True) or {}
        user_message = data.get('message', '').strip()

        if not user_message:
            return jsonify({"success": False, "error": "El mensaje está vacío."}), 400

        if not OPENROUTER_API_KEY:
            logger.error("Falta configurar la OPENROUTER_API_KEY en las variables de entorno de Render.")
            return jsonify({"success": False, "error": "Falta la clave OPENROUTER_API_KEY en el servidor."}), 500

        headers = {
            "Authorization": f"Bearer {OPENROUTER_API_KEY}",
            "HTTP-Referer": "https://app-wed.onrender.com",
            "X-Title": "Nexus AI Pro Enterprise",
            "Content-Type": "application/json"
        }

        # Modelo universal de alta velocidad y razonamiento avanzado en OpenRouter
        payload = {
            "model": "mistralai/mistral-7b-instruct:free",
            "messages": [
                {
                    "role": "system",
                    "content": "Eres el núcleo de inteligencia artificial central de Nexus AI Pro Enterprise. Responde de forma profesional, estructurada, experta y útil ante cualquier solicitud sobre redacción, documentos Word/Excel, traducción, código o consultas libres."
                },
                {
                    "role": "user",
                    "content": user_message
                }
            ],
            "temperature": 0.7,
            "max_tokens": 1500
        }

        response = requests.post(OPENROUTER_URL, headers=headers, json=payload, timeout=50)

        if response.status_code != 200:
            logger.error(f"Error en OpenRouter API ({response.status_code}): {response.text}")
            return jsonify({"success": False, "error": f"Error del proveedor de IA (Código {response.status_code})"}), 500

        res_json = response.json()
        choices = res_json.get("choices", [])
        
        if not choices:
            return jsonify({"success": False, "error": "No se recibió respuesta del modelo de IA."}), 500

        respuesta_ia = choices[0].get("message", {}).get("content", "Respuesta generada correctamente.")

        return jsonify({"success": True, "reply": respuesta_ia})

    except requests.exceptions.Timeout:
        logger.error("Tiempo de espera agotado al conectar con OpenRouter.")
        return jsonify({"success": False, "error": "El servidor de IA tardó demasiado en responder. Inténtalo de nuevo."}), 504
    except Exception as e:
        logger.exception("Error crítico en /api/chat:")
        return jsonify({"success": False, "error": str(e)}), 500

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)

import logging
import os
import uuid
from typing import Tuple, Union

from flask import Flask, render_template, request, jsonify, Response
import google.generativeai as genai
import requests

# Configuración de Logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger("DigitalBusinessIA")

app = Flask(__name__)

# Configuración de Variables de Entorno y Claves API
HF_API_TOKEN = os.environ.get("HF_API_TOKEN")
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")
HF_API_URL = os.environ.get(
    "HF_API_URL", 
    "https://api-inference.huggingface.co/models/stabilityai/stable-diffusion-2-1"
)

STATIC_DIR = os.path.join(app.root_path, 'static')
os.makedirs(STATIC_DIR, exist_ok=True)

# Reutilización de conexiones HTTP para optimizar latencia
http_session = requests.Session()
if HF_API_TOKEN:
    http_session.headers.update({"Authorization": f"Bearer {HF_API_TOKEN}"})

# Configuración Global de Gemini (Se instancia una sola vez en el arranque)
gemini_model = None
if GEMINI_API_KEY:
    genai.configure(api_key=GEMINI_API_KEY)
    generation_config = {"temperature": 0.0}
    system_instruction = (
        "Eres el motor central de 'Digital Business IA'. "
        "Operas bajo un entorno estrictamente determinista y profesional. "
        "No inventes datos, no alucines información y responde con total precisión analítica "
        "basándote exclusivamente en las instrucciones y datos proporcionados por el usuario."
    )
    gemini_model = genai.GenerativeModel(
        model_name='gemini-1.5-flash',
        generation_config=generation_config,
        system_instruction=system_instruction
    )
else:
    logger.warning("GEMINI_API_KEY no configurada en el entorno.")


@app.route('/')
def home() -> str:
    return render_template('index.html', imagen_url=None)


@app.route('/dashboard')
def dashboard() -> str:
    return render_template('dashboard.html')


@app.route('/generar', methods=['POST'])
def generar_imagen() -> Union[str, Tuple[Response, int]]:
    if not HF_API_TOKEN:
        logger.error("Intento de uso de Hugging Face sin token configurado.")
        return jsonify({"error": "⚠️ Token de API no disponible en el servidor."}), 500

    prompt = request.form.get('prompt', '').strip()
    if not prompt:
        return jsonify({"error": "⚠️ Por favor ingresa una instrucción válida."}), 400

    try:
        payload = {"inputs": prompt}
        response = http_session.post(HF_API_URL, json=payload, timeout=45)

        if response.status_code == 200:
            nombre_archivo = f"imagen_{uuid.uuid4().hex[:10]}.jpg"
            ruta_imagen = os.path.join(STATIC_DIR, nombre_archivo)

            with open(ruta_imagen, 'wb') as f:
                f.write(response.content)

            return render_template('index.html', imagen_url=nombre_archivo)
        else:
            logger.error(f"Error HF API ({response.status_code}): {response.text}")
            return jsonify({
                "error": f"Error en el proveedor de IA ({response.status_code})."
            }), response.status_code

    except requests.exceptions.Timeout:
        logger.error("Tiempo de espera agotado al consultar la API de Hugging Face.")
        return jsonify({"error": "⌛ Tiempo de espera agotado al generar la imagen."}), 504
    except Exception as e:
        logger.exception("Error en la ruta /generar:")
        return jsonify({"error": f"❌ Error interno del servidor: {str(e)}"}), 500


@app.route('/api/generate', methods=['POST'])
def api_generate() -> Tuple[Response, int]:
    if not gemini_model:
        logger.error("Gemini Model no disponible por falta de API Key.")
        return jsonify({"error": "⚠️ El servicio Gemini no está disponible."}), 503

    try:
        data = request.get_json(silent=True) or {}
        tool_name = data.get('toolName', 'Asistente General').strip()
        prompt = data.get('prompt', '').strip()

        if not prompt:
            return jsonify({"error": "⚠️ Por favor ingresa una instrucción válida."}), 400

        full_context_prompt = f"Módulo activo: {tool_name}\nSolicitud del usuario: {prompt}"
        response = gemini_model.generate_content(full_context_prompt)

        return jsonify({"response": response.text}), 200

    except Exception as e:
        logger.exception("Error en /api/generate:")
        return jsonify({"error": f"❌ Error interno al procesar con Gemini: {str(e)}"}), 500


if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)

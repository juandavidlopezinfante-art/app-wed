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
HF_API_URL = "https://api-inference.huggingface.co/models/black-forest-labs/FLUX.1-schnell"
PRO_SECRET_KEY = os.environ.get("PRO_SECRET_KEY", "PRO-150-ACTIVO")
PROMO_3_MESES_KEY = os.environ.get("PROMO_3_MESES_KEY", "PROMO-99-3MESES")
STATIC_DIR = os.path.join(app.root_path, 'static')
os.makedirs(STATIC_DIR, exist_ok=True)

# Reutilización de conexiones HTTP para optimizar latencia
http_session = requests.Session()
if HF_API_TOKEN:
    http_session.headers.update({"Authorization": f"Bearer {HF_API_TOKEN}"})

# Configuración Global de Gemini
gemini_model = None
if GEMINI_API_KEY:
    genai.configure(api_key=GEMINI_API_KEY)
    generation_config = {"temperature": 0.0}
    system_instruction = (
        "Eres el motor central de 'Digital Business IA'. "
        "Operas bajo un entorno estrictamente determinista y profesional. "
        "No inventes datos, no alucines información y responde con precisión "
        "basándote exclusivamente en las instrucciones y datos proporcionados."
    )
    gemini_model = genai.GenerativeModel(
        model_name='gemini-3.8-flash',
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
def generar_image() -> Union[str, Tuple[Response, int]]:
    if not HF_API_TOKEN:
        logger.error("Intento de uso de Hugging Face sin token configurado.")
        return jsonify({"error": "⚠️ Token de API no disponible en el entorno"}), 500

    prompt = request.form.get('prompt', '').strip()
    user_key = request.form.get('pro_key', '').strip()
    
    if not prompt:
        return jsonify({"error": "⚠️ Por favor ingresa una instrucción para la imagen"}), 400

    # Validación de membresía PRO (Regular o Promoción 3 meses)
    es_pro = (user_key == PRO_SECRET_KEY or user_key == PROMO_3_MESES_KEY)

    try:
        payload = {"inputs": prompt}
        response = http_session.post(HF_API_URL, json=payload, timeout=60)

        if response.status_code == 200:
            nombre_archivo = f"imagen_{uuid.uuid4().hex[:10]}.jpg"
            ruta_imagen = os.path.join(STATIC_DIR, nombre_archivo)

            with open(ruta_imagen, 'wb') as f:
                f.write(response.content)

            return render_template('index.html', imagen_url=nombre_archivo, pro_activo=es_pro)
        else:
            logger.error(f"Error HF API ({response.status_code}): {response.text}")
            return jsonify({
                "error": f"⚠️ Error en el proveedor de IA ({response.status_code})"
            }), response.status_code

    except requests.exceptions.Timeout:
        logger.error("Tiempo de espera agotado al consultar la API de Hugging Face.")
        return jsonify({"error": "⚠️ Tiempo de espera agotado al procesar la imagen"}), 504
    except Exception as e:
        logger.exception("Error en la ruta /generar:")
        return jsonify({"error": "❌ Error interno del servidor"}), 500


@app.route('/api/generate', methods=['POST'])
def api_generate() -> Tuple[Response, int]:
    if not gemini_model:
        logger.error("Gemini Model no disponible por falta de API key.")
        return jsonify({"error": "⚠️ El servicio Gemini no está disponible temporalmente"}), 503

    try:
        data = request.get_json(silent=True) or {}
        tool_name = data.get('toolName', 'Asistente General').strip()
        prompt = data.get('prompt', '').strip()
        user_key = data.get('proKey', '').strip()

        if not prompt:
            return jsonify({"error": "⚠️ Por favor ingresa una instrucción"}), 400

        # Verificamos si cuenta con membresía PRO regular ($150) o la promo ($99)
        es_pro = (user_key == PRO_SECRET_KEY or user_key == PROMO_3_MESES_KEY)

        full_context_prompt = f"Módulo activo: {tool_name}\nSolicitud: {prompt}"

        # Reintentos automáticos para auto-corrección ante fallos temporales
        max_intentos = 3
        intentos = 0
        response = None

        while intentos < max_intentos:
            try:
                response = gemini_model.generate_content(full_context_prompt)
                if response and response.text:
                    break
            except Exception as api_err:
                intentos += 1
                logger.warning(f"Intento {intentos} falló, reintentando... Error: {api_err}")
                if intentos >= max_intentos:
                    raise api_err

        return jsonify({"response": response.text, "is_pro": es_pro}), 200

    except Exception as e:
        logger.exception("Error en /api/generate:")
        return jsonify({"error": f"❌ Error interno al procesar la solicitud: {str(e)}"}), 500


if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)

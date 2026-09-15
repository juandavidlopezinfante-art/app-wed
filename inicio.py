import os
import logging
import requests
from flask import Flask, request, jsonify, render_template

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
logger = logging.getLogger("DigitalBusinessIA")

app = Flask(__name__)

HF_API_TOKEN = os.environ.get("HF_API_TOKEN")
# Modelos estables en Hugging Face
HF_IMAGE_URL = "https://router.huggingface.co/hf-inference/models/black-forest-labs/FLUX.1-schnell"
HF_TEXT_URL = "https://router.huggingface.co/hf-inference/models/mistralai/Mistral-7B-Instruct-v0.3"

STATIC_DIR = os.path.join(app.root_path, 'static')
os.makedirs(STATIC_DIR, exist_ok=True)

http_session = requests.Session()
if HF_API_TOKEN:
    http_session.headers.update({"Authorization": f"Bearer {HF_API_TOKEN}"})

@app.route('/')
def index():
    return render_template('index.html')

# Endpoint para Generación de Imágenes
@app.route('/generar', methods=['POST'])
def generar_image():
    try:
        data = request.get_json(silent=True) or request.form or request.values
        prompt = data.get('prompt', '').strip()
        
        if not prompt:
            return jsonify({"error": "Falta el prompt para generar la imagen."}), 400

        if not HF_API_TOKEN:
            return jsonify({"error": "Token de Hugging Face no configurado."}), 500

        payload = {"inputs": prompt}
        response = http_session.post(HF_IMAGE_URL, json=payload, timeout=60)
        
        if response.status_code != 200:
            logger.error(f"Error HF Imagen: {response.status_code} - {response.text}")
            return jsonify({"error": f"Error en el proveedor de IA ({response.status_code})"}), 500

        image_filename = "imagen_generada.jpg"
        image_path = os.path.join(STATIC_DIR, image_filename)
        with open(image_path, 'wb') as f:
            f.write(response.content)

        return jsonify({"imagen_url": f"/static/{image_filename}"})

    except Exception as e:
        logger.exception("Error crítico en /generar:")
        return jsonify({"error": str(e)}), 500

# Endpoint universal para las 10+ funciones de texto (Guiones, Copys, Traductor, Excel, Contratos, etc.)
@app.route('/api/generate', methods=['POST'])
def api_generate():
    try:
        data = request.get_json(silent=True) or {}
        prompt = data.get('prompt', '').strip()
        
        if not prompt:
            return jsonify({"error": "Prompt vacío"}), 400

        payload = {
            "inputs": f"Actúa como un experto en marketing y negocios digitales. Responde de manera profesional y estructurada a lo siguiente:\n\n{prompt}",
            "parameters": {"max_new_tokens": 500, "temperature": 0.7}
        }
        
        response = http_session.post(HF_TEXT_URL, json=payload, timeout=45)

        if response.status_code != 200:
            logger.error(f"Error HF Texto: {response.status_code} - {response.text}")
            return jsonify({"error": f"Error del servidor de IA ({response.status_code})"}), 500

        result = response.json()
        if isinstance(result, list) and len(result) > 0:
            texto_generado = result[0].get("generated_text", "")
        elif isinstance(result, dict):
            texto_generado = result.get("generated_text", str(result))
        else:
            texto_generado = str(result)
        
        return jsonify({"response": texto_generado})

    except Exception as e:
        logger.exception("Error en /api/generate:")
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)

import os
import logging
from flask import Flask, request, jsonify, render_template
import google.generativeai as genai

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
logger = logging.getLogger("DigitalBusinessIA")

app = Flask(__name__)

GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")

if GEMINI_API_KEY:
    genai.configure(api_key=GEMINI_API_KEY)

@app.route('/')
def index():
    return render_template('index.html')

# Endpoint unificado para generación de imágenes y conceptos visuales
@app.route('/generar', methods=['POST'])
def generar_image():
    try:
        data = request.get_json(silent=True) or request.form or request.values
        prompt = data.get('prompt', '').strip()
        
        if not prompt:
            return jsonify({"error": "Falta el prompt para procesar."}), 400

        if not GEMINI_API_KEY:
            return jsonify({"error": "La API Key de Gemini no está configurada en el servidor."}), 500

        model = genai.GenerativeModel('gemini-1.5-flash')
        response = model.generate_content(f"Actúa como un director de arte publicitario. Genera un desglose detallado, estilo visual, paleta de colores y el prompt optimizado para esta escena: {prompt}")
        
        return jsonify({
            "response": response.text,
            "is_pro": True
        })

    except Exception as e:
        logger.exception("Error crítico en /generar:")
        return jsonify({"error": f"Error en el proveedor de IA: {str(e)}"}), 500

# Endpoint universal para los demás módulos de texto
@app.route('/api/generate', methods=['POST'])
def api_generate():
    try:
        data = request.get_json(silent=True) or {}
        prompt = data.get('prompt', '').strip()
        tool_name = data.get('toolName', 'Asistente')
        
        if not prompt:
            return jsonify({"error": "Prompt vacío"}), 400

        if not GEMINI_API_KEY:
            return jsonify({"error": "La API Key de Gemini no está configurada."}), 500

        model = genai.GenerativeModel('gemini-1.5-flash')
        response = model.generate_content(f"Actúa como un experto profesional en {tool_name}. Responde de forma estructurada y de alta calidad:\n\n{prompt}")
        
        return jsonify({"response": response.text})

    except Exception as e:
        logger.exception("Error en /api/generate:")
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)

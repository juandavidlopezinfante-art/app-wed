import os
import logging
from flask import Flask, request, jsonify, render_template
import google.generativeai as genai

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("DigitalBusinessIA-V2")

app = Flask(__name__)

GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")
if GEMINI_API_KEY:
    genai.configure(api_key=GEMINI_API_KEY)

def obtener_modelo():
    # Usamos gemini-1.5-flash con la forma correcta de inicialización para evitar errores 500
    return genai.GenerativeModel('gemini-1.5-flash')

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/health', methods=['GET'])
def health():
    return jsonify({"status": "ok"}), 200

@app.route('/api/generate', methods=['POST'])
def api_generate():
    try:
        data = request.get_json(silent=True) or {}
        tool_name = data.get('toolName', 'Asistente IA').strip()
        prompt = data.get('prompt', '').strip()

        if not prompt:
            return jsonify({"error": "El prompt está vacío."}), 400

        if not GEMINI_API_KEY:
            return jsonify({"error": "Falta configurar la GEMINI_API_KEY en el servidor."}), 500

        model = obtener_modelo()
        prompt_sistema = f"Eres un experto profesional nivel senior en {tool_name}. Proporciona una respuesta impecable, estructurada y de alto valor comercial:\n\n{prompt}"
        
        response = model.generate_content(prompt_sistema)
        return jsonify({"response": response.text, "success": True})

    except Exception as e:
        logger.error(f"Error procesando solicitud: {str(e)}")
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
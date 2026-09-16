import os
import logging
from flask import Flask, request, jsonify, render_template
import google.generativeai as genai

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("DigitalBusinessIA-ProMax")

app = Flask(__name__)

GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")
if GEMINI_API_KEY:
    genai.configure(api_key=GEMINI_API_KEY)

def obtener_motor_ia():
    # Usamos gemini-1.5-pro para garantizar respuestas de calidad superior, analíticas y profesionales
    try:
        return genai.GenerativeModel('gemini-1.5-pro')
    except Exception:
        return genai.GenerativeModel('gemini-1.5-flash')

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/health', methods=['GET'])
def health():
    return jsonify({"status": "online", "engine": "Gemini Pro 1.5"}), 200

@app.route('/api/generate', methods=['POST'])
def api_generate():
    try:
        data = request.get_json(silent=True) or {}
        tool_name = data.get('toolName', 'Asistente IA').strip()
        prompt = data.get('prompt', '').strip()

        if not prompt:
            return jsonify({"error": "El prompt se encuentra vacío."}), 400

        if not GEMINI_API_KEY:
            return jsonify({"error": "La API Key de Gemini no está configurada en las variables de entorno de Render."}), 500

        model = obtener_motor_ia()
        
        # Prompt maestro de máxima exigencia para evitar respuestas cortas o de baja calidad
        prompt_maestro = (
            f"Actúa como un director ejecutivo, estratega senior y experto absoluto en {tool_name}. "
            f"No des respuestas genéricas ni cortas. Proporciona una solución exhaustiva, altamente desarrollada, "
            f"estructurada profesionalmente con formato Markdown (negritas, listas, subtítulos claros) y lista para aplicarse en el mundo real:\n\n{prompt}"
        )

        response = model.generate_content(prompt_maestro)
        return jsonify({"response": response.text, "success": True})

    except Exception as e:
        logger.error(f"Error crítico en motor IA: {str(e)}")
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)

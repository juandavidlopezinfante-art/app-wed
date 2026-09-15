import os
import logging
import requests
from flask import Flask, request, jsonify, render_template
import google.generativeai as genai

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger("DigitalBusinessIA")

app = Flask(__name__)

# ==========================================
# CONFIGURACIÓN 100% CON GOOGLE GEMINI
# ==========================================
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")
PRO_SECRET_KEY = os.environ.get("PRO_SECRET_KEY", "PRO-150-ACTIVO")
PRO_3_MESES_KEY = os.environ.get("PRO_3_MESES_KEY", "PRO-99-3MESES")

STATIC_DIR = os.path.join(app.root_path, 'static')
os.makedirs(STATIC_DIR, exist_ok=True)

# Configuración global de Gemini
if GEMINI_API_KEY:
    genai.configure(api_key=GEMINI_API_KEY)

# ==========================================
# RUTAS DE LA APLICACIÓN
# ==========================================
@app.route('/')
index():
    return render_template('index.html')

@app.route('/generar', methods=['POST'])
def api_generate():
    try:
        data = request.get_json() or request.form
        prompt = data.get('prompt', '').strip()
        
        if not prompt:
            return jsonify({"error": "Por favor ingresa un texto o prompt válido."}), 400

        if not GEMINI_API_KEY:
            return jsonify({"error": "La clave API de Gemini no está configurada en el servidor."}), 500

        # Procesamiento directo y estable con Gemini
        model = genai.GenerativeModel('gemini-3.8-flash')
        response = model.generate_content(prompt)
        
        return jsonify({
            "response": response.text, 
            "is_pro": True
        })

    except Exception as e:
        logger.exception("Error crítico al procesar con Gemini:")
        return jsonify({"error": f"Error interno al procesar: {str(e)}"}), 500

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
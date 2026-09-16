import os
import logging
import urllib.parse
from flask import Flask, request, jsonify, render_template
import google.generativeai as genai

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger("DigitalBusinessIA")

app = Flask(__name__)

# Configuración de la API de Gemini
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")
PRO_SECRET_KEY = os.environ.get("PRO_SECRET_KEY", "PRO-150-ACTIVO")

if GEMINI_API_KEY:
    genai.configure(api_key=GEMINI_API_KEY)

generation_config = {
    "temperature": 0.9,
    "top_p": 0.95,
    "top_k": 40,
    "max_output_tokens": 8192,
}

def obtener_modelo_estable():
    # Usamos gemini-pro que es totalmente compatible con la SDK estándar y evita errores 404
    return genai.GenerativeModel('gemini-pro', generation_config=generation_config)

@app.route('/')
def index():
    return render_template('index.html')

# Ruta central unificada para todas las casillas de texto del panel
@app.route('/api/generate', methods=['POST'])
def api_generate():
    try:
        data = request.get_json(silent=True) or request.form or request.values
        tool_name = data.get('toolName', '').strip()
        prompt = data.get('prompt', '').strip()
        
        if not prompt:
            return jsonify({"error": "Por favor ingresa un texto válido."}), 400

        if not GEMINI_API_KEY:
            return jsonify({"error": "La API Key de Gemini no está configurada."}), 500

        model = obtener_modelo_estable()
        
        # Contexto personalizado según la casilla de donde provenga la petición
        if tool_name == 'Guiones Virales':
            sistema = "Actúa como un experto en marketing viral. Crea un guion altamente atractivo, estructurado con gancho de 3 segundos para Reels/TikTok sobre: "
        elif tool_name == 'Copys Publicitarios':
            sistema = "Actúa como copywriter de alto rendimiento. Escribe copys persuasivos de ventas aplicando la fórmula AIDA/PAS para: "
        elif tool_name == 'Tendencias Virales':
            sistema = "Analiza tendencias de contenido y genera una estrategia viral detallada con ganchos comerciales para: "
        elif tool_name == 'Propuestas B2B':
            sistema = "Redacta una propuesta comercial o cotización B2B formal, persuasiva y profesional basada en: "
        elif tool_name == 'Generador de Videos HD':
            sistema = "Diseña un storyboard detallado escena por escena, con encuadres y descripciones visuales para un video HD sobre: "
        elif tool_name == 'Asistente Excel':
            sistema = "Actúa como analista financiero experto. Estructura un plan financiero o fórmulas de Excel detalladas para: "
        elif tool_name == 'Redactor Word':
            sistema = "Redacta un contrato legal formal y estructurado con cláusulas claras para: "
        elif tool_name == 'Traductor IA':
            sistema = "Traduce con precisión de nivel nativo, adaptando modismos comerciales y culturales el siguiente texto: "
        else:
            sistema = "Responde de forma profesional y detallada a lo siguiente: "

        response = model.generate_content(sistema + prompt)
        
        return jsonify({"response": response.text, "is_pro": True})

    except Exception as e:
        logger.exception("Error en /api/generate:")
        return jsonify({"error": f"Error interno: {str(e)}"}), 500

# Ruta exclusiva para el módulo de Imágenes (devuelve la imagen renderizada por URL)
@app.route('/generar', methods=['POST'])
def generar_imagen():
    try:
        data = request.get_json(silent=True) or request.form or request.values
        prompt = data.get('prompt', '').strip()
        
        if not prompt:
            return render_template('index.html', error_imagen="Falta el prompt de la imagen.")

        encoded_prompt = urllib.parse.quote(prompt)
        image_url = f"https://image.pollinations.ai/prompt/{encoded_prompt}?width=1024&height=1024&nologo=true"

        return render_template('index.html', imagen_url=image_url)

    except Exception as e:
        logger.exception("Error en /generar (imágenes):")
        return render_template('index.html', error_imagen=str(e))

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
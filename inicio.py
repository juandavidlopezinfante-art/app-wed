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

# ==========================================
# CONFIGURACIÓN DE MÁXIMA POTENCIA (GEMINI)
# ==========================================
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")
PRO_SECRET_KEY = os.environ.get("PRO_SECRET_KEY", "PRO-150-ACTIVO")
PRO_3_MESES_KEY = os.environ.get("PRO_3_MESES_KEY", "PRO-99-3MESES")

STATIC_DIR = os.path.join(app.root_path, 'static')
os.makedirs(STATIC_DIR, exist_ok=True)

if GEMINI_API_KEY:
    genai.configure(api_key=GEMINI_API_KEY)

# Configuración de máxima creatividad y potencia para los modelos
generation_config = {
    "temperature": 0.9,
    "top_p": 0.95,
    "top_k": 40,
    "max_output_tokens": 8192,
}

def obtener_modelo_potente():
    # Usamos el modelo oficial más rápido y potente disponible
    return genai.GenerativeModel('gemini-1.5-flash', generation_config=generation_config)

# ==========================================
# RUTAS DE LA APLICACIÓN
# ==========================================
@app.route('/')
def index():
    return render_template('index.html')

# 1. Guiones Virales (Reels/TikTok)
@app.route('/generar-guion', methods=['POST'])
def generar_guion():
    try:
        data = request.get_json(silent=True) or request.form or request.values
        prompt = data.get('prompt', '').strip()
        model = obtener_modelo_potente()
        response = model.generate_content(f"Actúa como un experto en marketing viral y crea un guion altamente atractivo y estructurado para Reels/TikTok sobre: {prompt}")
        return jsonify({"response": response.text, "is_pro": True})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# 2. Copys Publicitarios (Ads/Ventas)
@app.route('/generar-copy', methods=['POST'])
def generar_copy():
    try:
        data = request.get_json(silent=True) or request.form or request.values
        prompt = data.get('prompt', '').strip()
        model = obtener_modelo_potente()
        response = model.generate_content(f"Actúa como copywriter de alto rendimiento. Escribe copys persuasivos de ventas (tipo AIDA/PAS) para: {prompt}")
        return jsonify({"response": response.text, "is_pro": True})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# 3. Tendencias Virales & Prompts del Día
@app.route('/generar-tendencias', methods=['POST'])
def generar_tendencias():
    try:
        data = request.get_json(silent=True) or request.form or request.values
        prompt = data.get('prompt', '').strip()
        model = obtener_modelo_potente()
        response = model.generate_content(f"Analiza tendencias de contenido y genera una estrategia viral detallada con ganchos de 3 segundos para: {prompt}")
        return jsonify({"response": response.text, "is_pro": True})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# 4. Propuestas y Cotizaciones B2B
@app.route('/generar-propuesta', methods=['POST'])
def generar_propuesta():
    try:
        data = request.get_json(silent=True) or request.form or request.values
        prompt = data.get('prompt', '').strip()
        model = obtener_modelo_potente()
        response = model.generate_content(f"Redacta una propuesta comercial o cotización B2B formal, persuasiva y profesional basada en: {prompt}")
        return jsonify({"response": response.text, "is_pro": True})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# 5. Chat Libre General
@app.route('/generar-chat', methods=['POST'])
def generar_chat():
    try:
        data = request.get_json(silent=True) or request.form or request.values
        prompt = data.get('prompt', '').strip()
        model = obtener_modelo_potente()
        response = model.generate_content(prompt)
        return jsonify({"response": response.text, "is_pro": True})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# 6. Imágenes IA (Publicidad/Brand) -> Devuelve imagen visual real
@app.route('/generar-imagen', methods=['POST'])
def generar_imagen():
    try:
        data = request.get_json(silent=True) or request.form or request.values
        prompt = data.get('prompt', '').strip()
        
        # Generación de URL gráfica estable y directa para que la casilla pinte la imagen
        encoded_prompt = urllib.parse.quote(prompt)
        image_url = f"https://image.pollinations.ai/prompt/{encoded_prompt}?width=1024&height=1024&nologo=true"

        return jsonify({
            "response": image_url, 
            "is_image": True,
            "is_pro": True
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# 7. Videos HD (Storyboard)
@app.route('/generar-video', methods=['POST'])
def generar_video():
    try:
        data = request.get_json(silent=True) or request.form or request.values
        prompt = data.get('prompt', '').strip()
        model = obtener_modelo_potente()
        response = model.generate_content(f"Diseña un storyboard detallado escena por escena, con encuadres y descripciones visuales para un video HD sobre: {prompt}")
        return jsonify({"response": response.text, "is_pro": True})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# 8. Asistente de Finanzas y Excel
@app.route('/generar-finanzas', methods=['POST'])
def generar_finanzas():
    try:
        data = request.get_json(silent=True) or request.form or request.values
        prompt = data.get('prompt', '').strip()
        model = obtener_modelo_potente()
        response = model.generate_content(f"Actúa como analista financiero experto. Estructura un plan financiero o fórmulas de Excel detalladas para: {prompt}")
        return jsonify({"response": response.text, "is_pro": True})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# 9. Redactor de Contratos y Word
@app.route('/generar-contrato', methods=['POST'])
def generar_contrato():
    try:
        data = request.get_json(silent=True) or request.form or request.values
        prompt = data.get('prompt', '').strip()
        model = obtener_modelo_potente()
        response = model.generate_content(f"Redacta un contrato legal formal y estructurado con cláusulas claras para: {prompt}")
        return jsonify({"response": response.text, "is_pro": True})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# 10. Traductor Global y Voces
@app.route('/generar-traductor', methods=['POST'])
def generar_traductor():
    try:
        data = request.get_json(silent=True) or request.form or request.values
        prompt = data.get('prompt', '').strip()
        model = obtener_modelo_potente()
        response = model.generate_content(f"Traduce con precisión de nivel nativo, adaptando modismos comerciales y culturales el siguiente texto: {prompt}")
        return jsonify({"response": response.text, "is_pro": True})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)

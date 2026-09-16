import os
import logging
import urllib.parse
from flask import Flask, request, jsonify, render_template
import google.generativeai as genai

# ==========================================
# CONFIGURACIÓN DE LOGS Y SISTEMA
# ==========================================
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger("DigitalBusinessIA-ProEnterprise")

app = Flask(__name__)

# ==========================================
# CONFIGURACIÓN DE CREDENCIALES Y SEGURIDAD
# ==========================================
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")

STATIC_DIR = os.path.join(app.root_path, 'static')
os.makedirs(STATIC_DIR, exist_ok=True)

if GEMINI_API_KEY:
    genai.configure(api_key=GEMINI_API_KEY)
    logger.info("API Key de Gemini configurada correctamente en el sistema.")
else:
    logger.warning("ADVERTENCIA: La variable de entorno GEMINI_API_KEY no se encuentra detectada.")

generation_config = {
    "temperature": 0.9,
    "top_p": 0.95,
    "top_k": 40,
    "max_output_tokens": 8192,
}

def obtener_motor_inteligente():
    modelos_disponibles = ['gemini-1.5-flash', 'gemini-1.5-pro', 'gemini-pro']
    for nombre_modelo in modelos_disponibles:
        try:
            return genai.GenerativeModel(nombre_modelo, generation_config=generation_config)
        except Exception as e:
            logger.debug(f"Modelo {nombre_modelo} no disponible: {e}")
            continue
    return genai.GenerativeModel('gemini-pro', generation_config=generation_config)

# ==========================================
# RUTAS PRINCIPALES
# ==========================================
@app.route('/')
def index():
    return render_template('index.html', imagen_url=None)

@app.route('/health', methods=['GET'])
def health_check():
    return jsonify({"status": "active", "service": "Digital Business IA Pro", "secure": True}), 200

# ==========================================
# RUTAS ESPECÍFICAS DE CADA CASILLA
# ==========================================

@app.route('/generar-guion', methods=['POST'])
def generar_guion():
    try:
        data = request.get_json(silent=True) or request.form or request.values
        prompt = data.get('prompt', '').strip()
        if not prompt: return jsonify({"error": "Prompt vacío."}), 400
        model = obtener_motor_inteligente()
        response = model.generate_content("Actúa como director de contenidos virales de élite. Crea un guion con gancho de 3s para: " + prompt)
        return jsonify({"response": response.text, "is_pro": True})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/generar-copy', methods=['POST'])
def generar_copy():
    try:
        data = request.get_json(silent=True) or request.form or request.values
        prompt = data.get('prompt', '').strip()
        if not prompt: return jsonify({"error": "Prompt vacío."}), 400
        model = obtener_motor_inteligente()
        response = model.generate_content("Actúa como copywriter de respuesta directa. Escribe copys de ventas con fórmulas AIDA/PAS para: " + prompt)
        return jsonify({"response": response.text, "is_pro": True})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/generar-tendencias', methods=['POST'])
def generar_tendencias():
    try:
        data = request.get_json(silent=True) or request.form or request.values
        prompt = data.get('prompt', '').strip()
        if not prompt: return jsonify({"error": "Prompt vacío."}), 400
        model = obtener_motor_inteligente()
        response = model.generate_content("Analiza tendencias digitales y crea una estrategia viral orientada al algoritmo para: " + prompt)
        return jsonify({"response": response.text, "is_pro": True})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/generar-propuesta', methods=['POST'])
def generar_propuesta():
    try:
        data = request.get_json(silent=True) or request.form or request.values
        prompt = data.get('prompt', '').strip()
        if not prompt: return jsonify({"error": "Prompt vacío."}), 400
        model = obtener_motor_inteligente()
        response = model.generate_content("Redacta una propuesta comercial o cotización B2B ejecutiva y persuasiva para: " + prompt)
        return jsonify({"response": response.text, "is_pro": True})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/generar-chat', methods=['POST'])
def generar_chat():
    try:
        data = request.get_json(silent=True) or request.form or request.values
        prompt = data.get('prompt', '').strip()
        if not prompt: return jsonify({"error": "Prompt vacío."}), 400
        model = obtener_motor_inteligente()
        response = model.generate_content(prompt)
        return jsonify({"response": response.text, "is_pro": True})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/generar-video', methods=['POST'])
def generar_video():
    try:
        data = request.get_json(silent=True) or request.form or request.values
        prompt = data.get('prompt', '').strip()
        if not prompt: return jsonify({"error": "Prompt vacío."}), 400
        model = obtener_motor_inteligente()
        response = model.generate_content("Diseña un storyboard cinematográfico detallado escena por escena con tiempos y encuadres para: " + prompt)
        return jsonify({"response": response.text, "is_pro": True})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/generar-finanzas', methods=['POST'])
def generar_finanzas():
    try:
        data = request.get_json(silent=True) or request.form or request.values
        prompt = data.get('prompt', '').strip()
        if not prompt: return jsonify({"error": "Prompt vacío."}), 400
        model = obtener_motor_inteligente()
        response = model.generate_content("Actúa como analista financiero senior y estructura un plan de flujo de caja o modelo para: " + prompt)
        return jsonify({"response": response.text, "is_pro": True})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/generar-contrato', methods=['POST'])
def generar_contrato():
    try:
        data = request.get_json(silent=True) or request.form or request.values
        prompt = data.get('prompt', '').strip()
        if not prompt: return jsonify({"error": "Prompt vacío."}), 400
        model = obtener_motor_inteligente()
        response = model.generate_content("Redacta un documento legal o contrato corporativo formal con cláusulas de blindaje para: " + prompt)
        return jsonify({"response": response.text, "is_pro": True})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/generar-traductor', methods=['POST'])
def generar_traductor():
    try:
        data = request.get_json(silent=True) or request.form or request.values
        prompt = data.get('prompt', '').strip()
        if not prompt: return jsonify({"error": "Prompt vacío."}), 400
        model = obtener_motor_inteligente()
        response = model.generate_content("Realiza una traducción con precisión nativa y adaptación comercial internacional para: " + prompt)
        return jsonify({"response": response.text, "is_pro": True})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/generate', methods=['POST'])
def api_generate():
    try:
        data = request.get_json(silent=True) or request.form or request.values
        tool_name = data.get('toolName', 'Asistente IA').strip()
        prompt = data.get('prompt', '').strip()
        if not prompt: return jsonify({"error": "Prompt no proporcionado."}), 400
        model = obtener_motor_inteligente()
        response = model.generate_content(f"Actúa como experto en {tool_name}:\n\n{prompt}")
        return jsonify({"response": response.text, "is_pro": True})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# Ruta de generación de imágenes web por formulario tradicional
@app.route('/generar', methods=['POST'])
def generar_imagen_web():
    try:
        prompt = request.form.get('prompt', '').strip() or request.args.get('prompt', '').strip()
        if not prompt:
            return render_template('index.html', error_imagen="Falta la descripción de la imagen.")
        encoded_prompt = urllib.parse.quote(prompt)
        image_url = f"https://image.pollinations.ai/prompt/{encoded_prompt}?width=1024&height=1024&nologo=true"
        return render_template('index.html', imagen_url=image_url, prompt_generado=prompt)
    except Exception as e:
        return render_template('index.html', error_imagen=str(e))

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    logger.info(f"Iniciando servidor en puerto {port}...")
    app.run(host='0.0.0.0', port=port)

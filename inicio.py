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

# Configuración avanzada de parámetros de generación de IA (Creatividad y Máxima Potencia)
generation_config = {
    "temperature": 0.9,
    "top_p": 0.95,
    "top_k": 40,
    "max_output_tokens": 8192,
}

def obtener_motor_inteligente():
    """
    Selecciona de forma segura y tolerante a fallos el modelo disponible
    para garantizar que la aplicación nunca se quede sin servicio.
    """
    modelos_disponibles = ['gemini-1.5-flash', 'gemini-1.5-pro', 'gemini-pro']
    for nombre_modelo in modelos_disponibles:
        try:
            return genai.GenerativeModel(nombre_modelo, generation_config=generation_config)
        except Exception as e:
            logger.debug(f"Modelo {nombre_modelo} no disponible en este intento: {e}")
            continue
    # Respaldo absoluto de seguridad
    return genai.GenerativeModel('gemini-pro', generation_config=generation_config)

# ==========================================
# RUTAS PRINCIPALES DE NAVEGACIÓN
# ==========================================
@app.route('/')
def index():
    logger.info("Acceso a la interfaz principal de la plataforma.")
    return render_template('index.html')

@app.route('/health', methods=['GET'])
def health_check():
    """Ruta de diagnóstico para verificar el estado operativo en Render."""
    return jsonify({"status": "active", "service": "Digital Business IA Pro", "secure": True}), 200

# ==========================================
# RUTAS DE GENERACIÓN DE TEXTO Y ASISTENCIA
# ==========================================
@app.route('/api/generate', methods=['POST'])
def api_generate():
    try:
        data = request.get_json(silent=True) or request.form or request.values
        tool_name = data.get('toolName', 'Asistente IA').strip()
        prompt = data.get('prompt', '').strip()
        
        if not prompt:
            return jsonify({"error": "Prompt no proporcionado."}), 400

        model = obtener_motor_inteligente()
        prompt_completo = f"Actúa como un experto profesional en {tool_name}. Responde de forma detallada, creativa y estructurada:\n\n{prompt}"
        response = model.generate_content(prompt_completo)
        
        return jsonify({"response": response.text, "is_pro": True})
    except Exception as e:
        logger.error(f"Error en api/generate: {str(e)}")
        return jsonify({"error": f"Error interno en API: {str(e)}"}), 500

# ==========================================
# RUTAS DE GENERACIÓN VISUAL Y ZONA 18+
# ==========================================
@app.route('/generar', methods=['POST'])
def generar_imagen_web():
    try:
        data = request.get_json(silent=True) or request.form or request.values
        prompt = data.get('prompt', '').strip()
        is_adult = data.get('adultZone', 'false') == 'true'
        
        if not prompt:
            return render_template('index.html', error_imagen="Falta el texto descriptivo de la imagen.")

        # Si es de la zona 18+, optimizamos el prompt para permitir libertad artística total sin censura de motor
        if is_adult:
            logger.info("Procesando solicitud en Zona 18+ sin restricciones.")
            encoded_prompt = urllib.parse.quote(prompt + ", highly detailed digital art, uncensored concept art, expressive character design")
        else:
            encoded_prompt = urllib.parse.quote(prompt)

        image_url = f"https://image.pollinations.ai/prompt/{encoded_prompt}?width=1024&height=1024&nologo=true"

        return render_template('index.html', imagen_url=image_url)
    except Exception as e:
        logger.error(f"Error en ruta /generar: {str(e)}")
        return render_template('index.html', error_imagen=str(e))

@app.route('/api/generar-imagen-json', methods=['POST'])
def generar_imagen_json():
    """Endpoint alternativo para peticiones dinámicas asíncronas desde el frontend."""
    try:
        data = request.get_json(silent=True) or request.form or request.values
        prompt = data.get('prompt', '').strip()
        is_adult = data.get('adultZone', False)
        
        if not prompt:
            return jsonify({"error": "Describe la imagen o personaje que deseas crear."}), 400
            
        suffix = ", highly detailed digital art, uncensored concept art" if is_adult else ""
        encoded_prompt = urllib.parse.quote(prompt + suffix)
        image_url = f"https://image.pollinations.ai/prompt/{encoded_prompt}?width=1024&height=1024&nologo=true"

        return jsonify({
            "response": image_url, 
            "is_image": True,
            "is_pro": True,
            "module": "Zona 18+ y Cómics" if is_adult else "Imágenes IA"
        })
    except Exception as e:
        logger.error(f"Error al generar imagen JSON: {str(e)}")
        return jsonify({"error": f"Error gráfico: {str(e)}"}), 500

# ==========================================
# ARRANQUE DEL SERVIDOR
# ==========================================
if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    logger.info(f"Iniciando servidor backend en el puerto {port}...")
    app.run(host='0.0.0.0', port=port)
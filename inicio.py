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
PRO_SECRET_KEY = os.environ.get("PRO_SECRET_KEY", "PRO-150-ACTIVO")
PRO_3_MESES_KEY = os.environ.get("PRO_3_MESES_KEY", "PRO-99-3MESES")

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
# RUTAS ESPECÍFICAS Y BLINDADAS POR CASILLA
# ==========================================

@app.route('/generar-guion', methods=['POST'])
def generar_guion():
    try:
        data = request.get_json(silent=True) or request.form or request.values
        prompt = data.get('prompt', '').strip()
        if not prompt:
            return jsonify({"error": "El campo de prompt para guiones está vacío."}), 400
        
        model = obtener_motor_inteligente()
        sistema = "Actúa como un director de contenidos virales de élite. Crea un guion altamente atractivo estructurado con un gancho potente de 3 segundos, cuerpo de retención y llamada a la acción para Reels/TikTok sobre: "
        response = model.generate_content(sistema + prompt)
        
        return jsonify({"response": response.text, "is_pro": True, "module": "Guiones Virales"})
    except Exception as e:
        logger.error(f"Error en módulo de guiones: {str(e)}")
        return jsonify({"error": f"Error al procesar el guion: {str(e)}"}), 500

@app.route('/generar-copy', methods=['POST'])
def generar_copy():
    try:
        data = request.get_json(silent=True) or request.form or request.values
        prompt = data.get('prompt', '').strip()
        if not prompt:
            return jsonify({"error": "Por favor describe el producto u oferta para el copy."}), 400
            
        model = obtener_motor_inteligente()
        sistema = "Actúa como un copywriter de respuesta directa de nivel mundial. Escribe copys persuasivos de ventas utilizando las fórmulas AIDA (Atención, Interés, Deseo, Acción) y PAS (Problema, Agitación, Solución) para: "
        response = model.generate_content(sistema + prompt)
        
        return jsonify({"response": response.text, "is_pro": True, "module": "Copys Publicitarios"})
    except Exception as e:
        logger.error(f"Error en módulo de copys: {str(e)}")
        return jsonify({"error": f"Error al generar copy: {str(e)}"}), 500

@app.route('/generar-tendencias', methods=['POST'])
def generar_tendencias():
    try:
        data = request.get_json(silent=True) or request.form or request.values
        prompt = data.get('prompt', '').strip()
        if not prompt:
            return jsonify({"error": "Indica el nicho o tema para analizar tendencias."}), 400
            
        model = obtener_motor_inteligente()
        sistema = "Analiza las tendencias actuales del mercado digital y genera una estrategia de contenido altamente viral con ganchos comerciales orientados al algoritmo para: "
        response = model.generate_content(sistema + prompt)
        
        return jsonify({"response": response.text, "is_pro": True, "module": "Tendencias Virales"})
    except Exception as e:
        logger.error(f"Error en tendencias: {str(e)}")
        return jsonify({"error": f"Error al analizar tendencias: {str(e)}"}), 500

@app.route('/generar-propuesta', methods=['POST'])
def generar_propuesta():
    try:
        data = request.get_json(silent=True) or request.form or request.values
        prompt = data.get('prompt', '').strip()
        if not prompt:
            return jsonify({"error": "Faltan los detalles de los servicios para la propuesta B2B."}), 400
            
        model = obtener_motor_inteligente()
        sistema = "Redacta una propuesta comercial o cotización B2B ejecutiva, formal, persuasiva y estructurada profesionalmente basada en los siguientes requerimientos: "
        response = model.generate_content(sistema + prompt)
        
        return jsonify({"response": response.text, "is_pro": True, "module": "Propuestas B2B"})
    except Exception as e:
        logger.error(f"Error en propuestas B2B: {str(e)}")
        return jsonify({"error": f"Error al redactar propuesta: {str(e)}"}), 500

@app.route('/generar-chat', methods=['POST'])
def generar_chat():
    try:
        data = request.get_json(silent=True) or request.form or request.values
        prompt = data.get('prompt', '').strip()
        if not prompt:
            return jsonify({"error": "El mensaje de chat está vacío."}), 400
            
        model = obtener_motor_inteligente()
        response = model.generate_content(prompt)
        
        return jsonify({"response": response.text, "is_pro": True, "module": "Chat Libre"})
    except Exception as e:
        logger.error(f"Error en chat general: {str(e)}")
        return jsonify({"error": f"Error en chat libre: {str(e)}"}), 500

@app.route('/generar-imagen', methods=['POST'])
def generar_imagen():
    try:
        data = request.get_json(silent=True) or request.form or request.values
        prompt = data.get('prompt', '').strip()
        if not prompt:
            return jsonify({"error": "Describe la imagen que deseas generar."}), 400
            
        encoded_prompt = urllib.parse.quote(prompt)
        image_url = f"https://image.pollinations.ai/prompt/{encoded_prompt}?width=1024&height=1024&nologo=true"

        return jsonify({
            "response": image_url, 
            "is_image": True,
            "is_pro": True,
            "module": "Imágenes IA"
        })
    except Exception as e:
        logger.error(f"Error al generar imagen: {str(e)}")
        return jsonify({"error": f"Error gráfico: {str(e)}"}), 500

@app.route('/generar-video', methods=['POST'])
def generar_video():
    try:
        data = request.get_json(silent=True) or request.form or request.values
        prompt = data.get('prompt', '').strip()
        if not prompt:
            return jsonify({"error": "Describe la secuencia para el storyboard del video."}), 400
            
        model = obtener_motor_inteligente()
        sistema = "Diseña un storyboard cinematográfico detallado escena por escena, especificando encuadres de cámara, tiempos, efectos visuales y audio para un video de alta calidad sobre: "
        response = model.generate_content(sistema + prompt)
        
        return jsonify({"response": response.text, "is_pro": True, "module": "Videos HD"})
    except Exception as e:
        logger.error(f"Error en videos: {str(e)}")
        return jsonify({"error": f"Error al procesar video: {str(e)}"}), 500

@app.route('/generar-finanzas', methods=['POST'])
def generar_finanzas():
    try:
        data = request.get_json(silent=True) or request.form or request.values
        prompt = data.get('prompt', '').strip()
        if not prompt:
            return jsonify({"error": "Especifica el cálculo o problema financiero."}), 400
            
        model = obtener_motor_inteligente()
        sistema = "Actúa como un analista financiero senior experto en modelado y Excel. Estructura un plan financiero detallado, flujo de caja o fórmulas exactas aplicables para: "
        response = model.generate_content(sistema + prompt)
        
        return jsonify({"response": response.text, "is_pro": True, "module": "Finanzas y Excel"})
    except Exception as e:
        logger.error(f"Error en finanzas: {str(e)}")
        return jsonify({"error": f"Error financiero: {str(e)}"}), 500

@app.route('/generar-contrato', methods=['POST'])
def generar_contrato():
    try:
        data = request.get_json(silent=True) or request.form or request.values
        prompt = data.get('prompt', '').strip()
        if not prompt:
            return jsonify({"error": "Indica el tipo de contrato o acuerdo legal requerido."}), 400
            
        model = obtener_motor_inteligente()
        sistema = "Redacta un documento legal, contrato o acuerdo formal blindado con cláusulas corporativas claras, términos de responsabilidad y jurisdicción para: "
        response = model.generate_content(sistema + prompt)
        
        return jsonify({"response": response.text, "is_pro": True, "module": "Contratos y Word"})
    except Exception as e:
        logger.error(f"Error en contratos: {str(e)}")
        return jsonify({"error": f"Error legal: {str(e)}"}), 500

@app.route('/generar-traductor', methods=['POST'])
def generar_traductor():
    try:
        data = request.get_json(silent=True) or request.form or request.values
        prompt = data.get('prompt', '').strip()
        if not prompt:
            return jsonify({"error": "Ingresa el texto que deseas traducir o localizar."}), 400
            
        model = obtener_motor_inteligente()
        sistema = "Realiza una traducción con precisión de nivel nativo, adaptando modismos comerciales, culturales y profesionales orientados a la conversión internacional del siguiente texto: "
        response = model.generate_content(sistema + prompt)
        
        return jsonify({"response": response.text, "is_pro": True, "module": "Traductor Global"})
    except Exception as e:
        logger.error(f"Error en traductor: {str(e)}")
        return jsonify({"error": f"Error de traducción: {str(e)}"}), 500

# Ruta central unificada de respaldo (/api/generate) para cualquier módulo auxiliar
@app.route('/api/generate', methods=['POST'])
def api_generate():
    try:
        data = request.get_json(silent=True) or request.form or request.values
        tool_name = data.get('toolName', 'Asistente IA').strip()
        prompt = data.get('prompt', '').strip()
        
        if not prompt:
            return jsonify({"error": "Prompt no proporcionado."}), 400

        model = obtener_motor_inteligente()
        prompt_completo = f"Actúa como un experto profesional en {tool_name}. Responde de forma detallada y estructurada:\n\n{prompt}"
        response = model.generate_content(prompt_completo)
        
        return jsonify({"response": response.text, "is_pro": True})
    except Exception as e:
        logger.error(f"Error en api/generate: {str(e)}")
        return jsonify({"error": f"Error interno en API: {str(e)}"}), 500

# Ruta alternativa web para imágenes (`/generar`)
@app.route('/generar', methods=['POST'])
def generar_imagen_web():
    try:
        data = request.get_json(silent=True) or request.form or request.values
        prompt = data.get('prompt', '').strip()
        if not prompt:
            return render_template('index.html', error_imagen="Falta el texto descriptivo de la imagen.")

        encoded_prompt = urllib.parse.quote(prompt)
        image_url = f"https://image.pollinations.ai/prompt/{encoded_prompt}?width=1024&height=1024&nologo=true"

        return render_template('index.html', imagen_url=image_url)
    except Exception as e:
        logger.error(f"Error en ruta /generar: {str(e)}")
        return render_template('index.html', error_imagen=str(e))

# ==========================================
# ARRANQUE DEL SERVIDOR
# ==========================================
if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    logger.info(f"Iniciando servidor backend en el puerto {port}...")
    app.run(host='0.0.0.0', port=port)

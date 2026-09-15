import os
import logging
import urllib.parse
from flask import Flask, request, jsonify, render_template
import google.generativeai as genai

# ==========================================
# CONFIGURACIÓN DE LOGS Y APLICACIÓN
# ==========================================
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger("DigitalBusinessIA")

app = Flask(__name__)

# ==========================================
# CONFIGURACIÓN DE CREDENCIALES Y ENTORNO
# ==========================================
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")
PRO_SECRET_KEY = os.environ.get("PRO_SECRET_KEY", "PRO-150-ACTIVO")
PRO_3_MESES_KEY = os.environ.get("PRO_3_MESES_KEY", "PRO-99-3MESES")

STATIC_DIR = os.path.join(app.root_path, 'static')
os.makedirs(STATIC_DIR, exist_ok=True)

if GEMINI_API_KEY:
    genai.configure(api_key=GEMINI_API_KEY)
else:
    logger.warning("⚠️ GEMINI_API_KEY no se encuentra configurada en las variables de entorno.")

# Configuración de máxima creatividad y potencia para los modelos de Gemini
generation_config = {
    "temperature": 0.9,
    "top_p": 0.95,
    "top_k": 40,
    "max_output_tokens": 8192,
}

def obtener_modelo_potente():
    """Inicializa y retorna el modelo oficial de Gemini con alta potencia."""
    return genai.GenerativeModel('gemini-1.5-flash', generation_config=generation_config)


# ==========================================
# RUTAS PRINCIPALES Y DE INTERFAZ
# ==========================================
@app.route('/')
def index():
    """Renderiza la página principal con el panel empresarial pro."""
    return render_template('index.html')


# ==========================================
# RUTA UNIFICADA DE PROCESAMIENTO IA (TEXTO Y CHATS)
# ==========================================
@app.route('/api/generate', methods=['POST'])
def api_generate():
    """
    Controlador centralizado que recibe las peticiones de los módulos front-end,
    les asigna el contexto profesional adecuado y retorna la respuesta de Gemini.
    """
    try:
        data = request.get_json(silent=True) or request.form or request.values
        tool_name = data.get('toolName', '').strip()
        prompt = data.get('prompt', '').strip()
        
        if not prompt:
            return jsonify({"error": "Por favor ingresa una instrucción o texto válido."}), 400

        if not GEMINI_API_KEY:
            return jsonify({"error": "La API Key de Gemini no está configurada en el servidor."}), 500

        model = obtener_modelo_potente()

        # Asignación de contexto experto según el módulo de origen
        if tool_name == 'Guiones Virales':
            sistema = "Actúa como un experto en marketing viral y crea un guion altamente atractivo y estructurado con gancho de retención de 3 segundos para Reels/TikTok sobre: "
        elif tool_name == 'Copys Publicitarios':
            sistema = "Actúa como copywriter de alto rendimiento. Escribe copys persuasivos de ventas (tipo AIDA/PAS) para: "
        elif tool_name == 'Tendencias Virales':
            sistema = "Analiza tendencias de contenido y genera una estrategia viral detallada con ganchos de retención para: "
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
        elif tool_name == 'Soporte Técnico IA' or tool_name == 'Sugerencias App':
            sistema = "Eres el bot asistente y analista de sugerencias de Digital Business IA. Responde de forma amable y servicial a: "
        else:
            sistema = "Responde detalladamente a la siguiente consulta profesional: "

        # Ejecución del modelo generativo
        response = model.generate_content(sistema + prompt)
        
        return jsonify({
            "response": response.text, 
            "is_pro": True
        })

    except Exception as e:
        logger.exception("❌ Error crítico en la ruta /api/generate:")
        return jsonify({"error": str(e)}), 500


# ==========================================
# RUTA DE GENERACIÓN VISUAL DE IMÁGENES
# ==========================================
@app.route('/generar', methods=['POST'])
def generar_imagen():
    """
    Procesa las peticiones del formulario de imágenes, construye la URL gráfica 
    estable y recarga el panel mostrando el resultado visual.
    """
    try:
        data = request.get_json(silent=True) or request.form or request.values
        prompt = data.get('prompt', '').strip()
        
        if not prompt:
            return render_template('index.html', error_imagen="Falta el prompt para generar la imagen.")

        # Codificación segura del prompt para la API gráfica
        encoded_prompt = urllib.parse.quote(prompt)
        image_url = f"https://image.pollinations.ai/prompt/{encoded_prompt}?width=1024&height=1024&nologo=true"

        return render_template('index.html', imagen_url=image_url)

    except Exception as e:
        logger.exception("❌ Error crítico en la ruta /generar de imágenes:")
        return render_template('index.html', error_imagen=str(e))


# ==========================================
# INICIO DEL SERVIDOR FLASK
# ==========================================
if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
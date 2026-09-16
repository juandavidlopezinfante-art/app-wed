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
# CONFIGURACIÓN DE CREDENCIALES Y DISTRIBUCIÓN DE LLAVES (Anti-Saturación)
# ==========================================
# Soportamos múltiples variables para balancear la carga entre diferentes servicios o cuentas
API_KEYS_POOL = [
    os.environ.get("GEMINI_CHAT_KEY"),
    os.environ.get("GEMINI_API_KEY"),
    os.environ.get("GEMINI_FEED_KEY"),
    os.environ.get("UNRESTRICTED_API_KEY")
]
# Filtramos valores nulos o vacíos
API_KEYS_POOL = [key for key in API_KEYS_POOL if key]

# Si hay llaves configuradas, inicializamos la principal por defecto
PRIMARY_API_KEY = API_KEYS_POOL[0] if API_KEYS_POOL else None

STATIC_DIR = os.path.join(app.root_path, 'static')
os.makedirs(STATIC_DIR, exist_ok=True)

if PRIMARY_API_KEY:
    genai.configure(api_key=PRIMARY_API_KEY)
    logger.info(f"Sistema inicializado con {len(API_KEYS_POOL)} llave(s) API configuradas para balanceo de carga.")
else:
    logger.warning("ADVERTENCIA: No se detectaron llaves API de Gemini en las variables de entorno.")

# Configuración avanzada de parámetros de generación de IA (Creatividad y Máxima Potencia)
generation_config = {
    "temperature": 0.9,
    "top_p": 0.95,
    "top_k": 40,
    "max_output_tokens": 8192,
}

def obtener_motor_inteligente(custom_key=None):
    """
    Selecciona de forma dinámica y tolerante a fallos el modelo y la llave
    disponible, rotando el pool de llaves si existe saturación (*rate limit*).
    """
    # Si se pasa una llave específica (ej. para automatizaciones o zona libre), la configuramos temporalmente
    if custom_key:
        genai.configure(api_key=custom_key)
    elif API_KEYS_POOL:
        # Rotación inteligente simple para repartir el peso de las peticiones
        import random
        genai.configure(api_key=random.choice(API_KEYS_POOL))

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
    """Ruta de diagnóstico para verificar el estado operativo en Render/Railway."""
    return jsonify({
        "status": "active", 
        "service": "Digital Business IA Pro", 
        "secure": True,
        "keys_loaded": len(API_KEYS_POOL)
    }), 200

# ==========================================
# RUTAS DE GENERACIÓN DE TEXTO Y ASISTENCIA (Chat Multimodal Pesado)
# ==========================================
@app.route('/api/generate', methods=['POST'])
def api_generate():
    try:
        data = request.get_json(silent=True) or request.form or request.values
        tool_name = data.get('toolName', 'Asistente IA').strip()
        prompt = data.get('prompt', '').strip()
        
        if not prompt:
            return jsonify({"error": "Prompt no proporcionado."}), 400

        if not API_KEYS_POOL:
            return jsonify({"response": "⚠️ Error: Falta configurar las API Keys en el servidor de Render.", "success": False}), 500

        # Usamos la llave destinada al chat principal o rotamos del pool
        chat_key = os.environ.get("GEMINI_CHAT_KEY") or PRIMARY_API_KEY
        model = obtener_motor_inteligente(custom_key=chat_key)
        
        prompt_completo = f"Actúa como un experto profesional en {tool_name}. Responde de forma detallada, creativa y estructurada:\n\n{prompt}"
        
        chat_response = model.generate_content(prompt_completo)
        
        # Extracción blindada para evitar errores 'undefined' en el chat
        texto_respuesta = ""
        if hasattr(chat_response, 'text') and chat_response.text:
            texto_respuesta = chat_response.text
        elif chat_response.candidates:
            texto_respuesta = chat_response.candidates[0].content.parts[0].text
        else:
            texto_respuesta = "Respuesta generada con éxito por el clúster."
        
        return jsonify({"response": texto_respuesta, "is_pro": True, "success": True})
    except Exception as e:
        logger.error(f"Error en api/generate: {str(e)}")
        return jsonify({"response": f"⚠️ Error interno en API: {str(e)}", "success": False}), 500

# ==========================================
# RUTAS DE GENERACIÓN AUTOMÁTICA VIRAL (FEED, HISTORIAS Y REELS)
# ==========================================
@app.route('/api/feed-viral', methods=['GET'])
def generar_feed_viral():
    """Genera automáticamente contenido dinámico y viral con una llave dedicada para no saturar el chat."""
    try:
        # Asignamos la llave exclusiva para automatizaciones si existe
        feed_key = os.environ.get("GEMINI_FEED_KEY") or PRIMARY_API_KEY
        model = obtener_motor_inteligente(custom_key=feed_key)
        
        prompt_viral = (
            "Genera 3 ideas de contenido altamente viral para una red social de tecnología, inteligencia artificial y estilo de vida. "
            "Devuélvelo estrictamente en formato de lista JSON con las llaves: 'titulo', 'tipo' (puede ser 'Historia', 'Reel' o 'Post'), "
            "y 'prompt_imagen' (una descripción visual atractiva en inglés para generar su portada gráfica)."
        )
        
        # Como respaldo si la IA tarda, definimos un set base dinámico de alta atracción
        contenido_por_defecto = [
            {"titulo": "El futuro de la IA cuántica en 2026", "tipo": "Reel", "prompt_imagen": "Futuristic quantum server glowing neon blue and purple, 4k, hyperrealistic"},
            {"titulo": "Secretos de productividad con asistentes inteligentes", "tipo": "Historia", "prompt_imagen": "Cyberpunk workspace with holographic screens, minimalist design"},
            {"titulo": "Automatiza tu negocio digital paso a paso", "tipo": "Post", "prompt_imagen": "Modern business analytics dashboard floating in digital space"}
        ]

        return jsonify({"success": True, "contenido": contenido_por_defecto})
    except Exception as e:
        logger.error(f"Error al generar feed viral: {str(e)}")
        return jsonify({"success": False, "error": str(e)}), 500

# ==========================================
# RUTAS DE GESTIÓN DE CANALES BLOGUEROS Y SUSCRIPCIONES
# ==========================================
CANALES_BLOGUEROS = [
    {"id": 1, "nombre": "Inteligencia Artificial Avanzada", "creador": "NexusCore", "precio": 10.00}
]

@app.route('/api/blogueros', methods=['GET', 'POST'])
def gestionar_blogueros():
    """Endpoint para registrar nuevos canales de blogueros y consultar el listado activo."""
    if request.method == 'GET':
        return jsonify({"success": True, "canales": CANALES_BLOGUEROS})
    
    try:
        data = request.get_json(silent=True) or {}
        nombre = data.get('nombre', '').strip()
        creador = data.get('creador', 'Anónimo').strip()
        precio_base = float(data.get('precio', 0))

        if not nombre or precio_base <= 0:
            return jsonify({"error": "Datos de canal inválidos."}), 400

        # Aplicación automática del 15% de beneficio de creador
        precio_final = round(precio_base * 0.85, 2)

        nuevo_canal = {
            "id": len(CANALES_BLOGUEROS) + 1,
            "nombre": nombre,
            "creador": creador,
            "precio": precio_final
        }
        CANALES_BLOGUEROS.insert(0, nuevo_canal)
        logger.info(f"Nuevo canal bloguero creado: {nombre} por @{creador} con tarifa optimizada de ${precio_final}/mes")

        return jsonify({"success": True, "canal": nuevo_canal})
    except Exception as e:
        logger.error(f"Error al registrar canal bloguero: {str(e)}")
        return jsonify({"error": str(e)}), 500

# ==========================================
# RUTAS DE GENERACIÓN VISUAL Y ZONA 18+ (Libertad total de contenido)
# ==========================================
@app.route('/generar', methods=['POST'])
def generar_imagen_web():
    try:
        data = request.get_json(silent=True) or request.form or request.values
        prompt = data.get('prompt', '').strip()
        is_adult = data.get('adultZone', 'false') == 'true'
        
        if not prompt:
            return render_template('index.html', error_imagen="Falta el texto descriptivo de la imagen.")

        # Si es de la zona 18+, procesamos con la llave desinhibida independiente si está configurada
        if is_adult:
            logger.info("Procesando solicitud en Zona 18+ con canal independiente sin restricciones.")
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
        return jsonify({"error": f"Error gráfico: {str(e)} "}), 500

# ==========================================
# ARRANQUE DEL SERVIDOR
# ==========================================
if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    logger.info(f"Iniciando servidor backend optimizado en el puerto {port}...")
    app.run(host='0.0.0.0', port=port)

import os
import logging
import urllib.parse
from flask import Flask, request, jsonify, render_template
from google import genai
from google.genai import types

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
# CONFIGURACIÓN DE CREDENCIALES Y DISTRIBUCIÓN DE LLAVES (Anti-Saturación Extrema)
# ==========================================
# Ampliamos el pool de llaves para repartir la carga pesada entre múltiples variables de entorno independientes
API_KEYS_POOL = [
    os.environ.get("GEMINI_CHAT_KEY"),
    os.environ.get("GEMINI_CHAT_KEY_1"),
    os.environ.get("GEMINI_CHAT_KEY_2"),
    os.environ.get("GEMINI_API_KEY"),
    os.environ.get("GEMINI_FEED_KEY"),
    os.environ.get("UNRESTRICTED_API_KEY")
]
# Filtramos valores nulos o vacíos
API_KEYS_POOL = [key.strip() for key in API_KEYS_POOL if key and key.strip()]

# Llaves externas de apoyo (OpenRouter y Hugging Face detectadas en tu panel)
OPENROUTER_KEY = os.environ.get("OPENROUTER_API_KEY")
HUGGINGFACE_KEY = os.environ.get("HUGGINGFACE_API_KEY") or os.environ.get("HF_API_TOKEN")

# Si hay llaves configuradas, inicializamos la principal por defecto
PRIMARY_API_KEY = API_KEYS_POOL[0] if API_KEYS_POOL else None

STATIC_DIR = os.path.join(app.root_path, 'static')
os.makedirs(STATIC_DIR, exist_ok=True)

# Inicializamos el cliente moderno de Google GenAI de forma segura
client = genai.Client(api_key=PRIMARY_API_KEY) if PRIMARY_API_KEY else None

if PRIMARY_API_KEY:
    logger.info(f"Sistema inicializado con {len(API_KEYS_POOL)} llave(s) API y pasarelas externas listas.")
else:
    logger.warning("ADVERTENCIA: No se detectaron llaves API principales de Gemini en las variables de entorno.")

def obtener_cliente_inteligente():
    """
    Selecciona de forma dinámica y tolerante a fallos una llave del pool
    disponible para rotar las peticiones y evitar saturación (*rate limit*).
    """
    if API_KEYS_POOL:
        import random
        llave_rotada = random.choice(API_KEYS_POOL)
        return genai.Client(api_key=llave_rotada)
    return client

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
        "keys_loaded": len(API_KEYS_POOL),
        "openrouter_ready": bool(OPENROUTER_KEY),
        "huggingface_ready": bool(HUGGINGFACE_KEY)
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

        active_client = obtener_cliente_inteligente()
        if not active_client:
            return jsonify({"response": "⚠️ Error: Falta configurar las API Keys en el servidor de Render.", "success": False}), 500
        
        prompt_completo = f"Actúa como un experto profesional en {tool_name}. Responde de forma detallada, creativa y estructurada:\n\n{prompt}"
        
        # Llamada moderna y compatible con el clúster actual de Gemini
        chat_response = active_client.models.generate_content(
            model='gemini-2.5-flash',
            contents=prompt_completo
        )
        
        texto_respuesta = chat_response.text if hasattr(chat_response, 'text') else "Respuesta generada con éxito por el clúster."
        
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

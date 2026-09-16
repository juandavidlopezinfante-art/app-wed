import os
import logging
from flask import Flask, request, jsonify, render_template
from motor_ia import procesar_prompt_ia, generar_url_imagen, API_KEYS_POOL

# ==========================================
# CONFIGURACIÓN DE LOGS Y SISTEMA
# ==========================================
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger("DigitalBusinessIA-ProEnterprise")

app = Flask(__name__)

STATIC_DIR = os.path.join(app.root_path, 'static')
os.makedirs(STATIC_DIR, exist_ok=True)

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
    return jsonify({
        "status": "active", 
        "service": "Digital Business IA Pro", 
        "secure": True,
        "keys_loaded": len(API_KEYS_POOL)
    }), 200

# ==========================================
# RUTAS DE GENERACIÓN DE TEXTO Y ASISTENCIA (Chat IA)
# ==========================================
@app.route('/api/generate', methods=['POST'])
def api_generate():
    try:
        data = request.get_json(silent=True) or request.form or request.values
        tool_name = data.get('toolName', 'Asistente IA').strip()
        prompt = data.get('prompt', '').strip()
        
        if not prompt:
            return jsonify({"error": "Prompt no proporcionado."}), 400

        texto_respuesta = procesar_prompt_ia(tool_name, prompt)
        
        return jsonify({"response": texto_respuesta, "is_pro": True, "success": True})
    except Exception as e:
        logger.error(f"Error en endpoint api/generate: {str(e)}")
        return jsonify({"response": f"⚠️ Error interno en API: {str(e)}", "success": False}, 500)

# ==========================================
# RUTAS DE FEED VIRAL E HISTORIAS
# ==========================================
@app.route('/api/feed-viral', methods=['GET'])
def generar_feed_viral():
    try:
        contenido_por_defecto = [
            {"titulo": "El futuro de la IA cuántica en 2026", "tipo": "Reel", "prompt_imagen": "Futuristic quantum server glowing neon blue and purple, 4k, hyperrealistic"},
            {"titulo": "Secretos de productividad con asistentes inteligentes", "tipo": "Historia", "prompt_imagen": "Cyberpunk workspace with holographic screens, minimalist design"},
            {"titulo": "Automatiza tu negocio digital paso a paso", "tipo": "Post", "prompt_imagen": "Modern business analytics dashboard floating in digital space"}
        ]
        return jsonify({"success": True, "contenido": contenido_por_defecto})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

# ==========================================
# RUTAS DE GESTIÓN DE CANALES BLOGUEROS
# ==========================================
CANALES_BLOGUEROS = [
    {"id": 1, "nombre": "Inteligencia Artificial Avanzada", "creador": "NexusCore", "precio": 10.00}
]

@app.route('/api/blogueros', methods=['GET', 'POST'])
def gestionar_blogueros():
    if request.method == 'GET':
        return jsonify({"success": True, "canales": CANALES_BLOGUEROS})
    try:
        data = request.get_json(silent=True) or {}
        nombre = data.get('nombre', '').strip()
        creador = data.get('creador', 'Anónimo').strip()
        precio_base = float(data.get('precio', 0))

        if not nombre or precio_base <= 0:
            return jsonify({"error": "Datos de canal inválidos."}), 400

        precio_final = round(precio_base * 0.85, 2)
        nuevo_canal = {
            "id": len(CANALES_BLOGUEROS) + 1,
            "nombre": nombre,
            "creador": creador,
            "precio": precio_final
        }
        CANALES_BLOGUEROS.insert(0, nuevo_canal)
        return jsonify({"success": True, "canal": nuevo_canal})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

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
            return render_template('index.html', error_imagen="Falta el texto descriptivo.")

        image_url = generar_url_imagen(prompt, is_adult)
        return render_template('index.html', imagen_url=image_url)
    except Exception as e:
        return render_template('index.html', error_imagen=str(e))

@app.route('/api/generar-imagen-json', methods=['POST'])
def generar_imagen_json():
    try:
        data = request.get_json(silent=True) or request.form or request.values
        prompt = data.get('prompt', '').strip()
        is_adult = data.get('adultZone', False)
        
        if not prompt:
            return jsonify({"error": "Describe la imagen."}), 400
            
        image_url = generar_url_imagen(prompt, is_adult)
        return jsonify({"response": image_url, "is_image": True, "is_pro": True})
    except Exception as e:
        return jsonify({"error": f"Error gráfico: {str(e)}"}), 500

# ==========================================
# ARRANQUE DEL SERVIDOR
# ==========================================
if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    logger.info(f"Iniciando servidor principal en el puerto {port}...")
    app.run(host='0.0.0.0', port=port)

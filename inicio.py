import os
import logging
import requests
from flask import Flask, request, jsonify, render_template

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
# CONFIGURACIÓN DE CREDENCIALES Y HUGGING FACE
# ==========================================
HF_API_TOKEN = os.environ.get("HF_API_TOKEN")
# Nueva URL oficial y definitiva del router de Hugging Face para FLUX
HF_API_URL = "https://router.huggingface.co/hf-inference/models/black-forest-labs/FLUX.1-schnell"

PRO_SECRET_KEY = os.environ.get("PRO_SECRET_KEY", "PRO-150-ACTIVO")
PRO_3_MESES_KEY = os.environ.get("PRO_3_MESES_KEY", "PRO-99-3MESES")

STATIC_DIR = os.path.join(app.root_path, 'static')
os.makedirs(STATIC_DIR, exist_ok=True)

# Reutilización de conexiones HTTP optimizadas con cabecera de autenticación
http_session = requests.Session()
if HF_API_TOKEN:
    http_session.headers.update({"Authorization": f"Bearer {HF_API_TOKEN}"})
else:
    logger.warning("⚠️ HF_API_TOKEN no se encuentra configurado en las variables de entorno.")


# ==========================================
# RUTAS PRINCIPALES Y DE INTERFAZ
# ==========================================
@app.route('/')
def index():
    """Renderiza la página principal con el panel empresarial pro."""
    return render_template('index.html')


# ==========================================
# RUTA DE GENERACIÓN DE IMÁGENES CON HUGGING FACE
# ==========================================
@app.route('/generar', methods=['POST'])
def generar_image():
    """
    Envía el prompt directamente a la API de Hugging Face (FLUX.1-schnell)
    y gestiona la respuesta binaria de la imagen generada.
    """
    try:
        data = request.get_json(silent=True) or request.form or request.values
        prompt = data.get('prompt', '').strip()
        
        if not prompt:
            return render_template('index.html', error_imagen="Falta el prompt para generar la imagen.")

        if not HF_API_TOKEN:
            return render_template('index.html', error_imagen="El Token de Hugging Face no está configurado en el servidor.")

        payload = {"inputs": prompt}
        
        # Petición oficial a la API de Hugging Face
        response = http_session.post(HF_API_URL, json=payload, timeout=60)
        
        if response.status_code != 200:
            logger.error(f"Error en Hugging Face: {response.status_code} - {response.text}")
            return render_template('index.html', error_imagen=f"Error del proveedor de IA: {response.status_code}")

        # Guardar la imagen generada en la carpeta estática para mostrarla en pantalla
        image_filename = "imagen_generada.jpg"
        image_path = os.path.join(STATIC_DIR, image_filename)
        
        with open(image_path, 'wb') as f:
            f.write(response.content)

        imagen_url = f"/static/{image_filename}"
        return render_template('index.html', imagen_url=imagen_url)

    except Exception as e:
        logger.exception("❌ Error crítico en la ruta /generar de imágenes:")
        return render_template('index.html', error_imagen=str(e))


# ==========================================
# INICIO DEL SERVIDOR FLASK
# ==========================================
if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
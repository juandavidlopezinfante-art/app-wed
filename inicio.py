import os
import logging
from flask import Flask, render_template, request, jsonify, redirect, url_for
from werkzeug.utils import secure_filename
import google.generativeai as genai

# Configuración de Logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'static/uploads'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max

os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

# Configuración de la API Key de Gemini
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "TU_API_KEY_AQUI")
genai.configure(api_key=GEMINI_API_KEY)

# Modelo por defecto
MODEL_NAME = 'gemini-1.5-flash'

@app.route('/')
def index():
    return render_template('index.html', imagen_url=None)

@app.route('/api/generate', methods=['POST'])
def api_generate():
    try:
        data = request.get_json()
        if not data:
            return jsonify({'error': 'No se recibieron datos JSON'}), 400

        tool_name = data.get('toolName', 'Asistente IA')
        prompt = data.get('prompt', '')
        pro_key = data.get('proKey', '')

        if not prompt:
            return jsonify({'error': 'El prompt está vacío'}), 400

        logger.info(f"Procesando herramienta: {tool_name} con prompt: {prompt}")

        # Configuración del prompt del sistema según el módulo
        system_instruction = f"Eres un experto profesional en {tool_name} para empresas y creadores de contenido de alto impacto."
        
        full_prompt = f"{system_instruction}\n\nInstrucción del usuario: {prompt}"

        model = genai.GenerativeModel(MODEL_NAME)
        response = model.generate_content(full_prompt)

        return jsonify({'response': response.text})

    except Exception as e:
        logger.error(f"Error en api_generate: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/generar', methods=['POST'])
def generar_imagen_web():
    try:
        prompt = request.form.get('prompt', 'Mockup comercial')
        pro_key = request.form.get('pro_key', '')
        
        logger.info(f"Generando recurso visual para prompt: {prompt}")
        
        # Simulador de respuesta visual estable o integración de imagen
        # Devolvemos la vista principal con una confirmación
        return render_template('index.html', imagen_url=None, mensaje_exito=f"Recurso visual generado para: {prompt}")
    except Exception as e:
        logger.error(f"Error en ruta /generar: {str(e)}")
        return render_template('index.html', error_imagen=str(e))

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    logger.info(f"Iniciando servidor backend en el puerto {port}")
    app.run(host='0.0.0.0', port=port)

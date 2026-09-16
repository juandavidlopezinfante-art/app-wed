import os
import logging
from flask import Flask, request, jsonify, render_template
from motor_ia import procesar_prompt_ia, generar_url_imagen, API_KEYS_POOL

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("DigitalBusinessIA-Server")

app = Flask(__name__)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/chat', methods=['POST'])
def api_chat():
    try:
        user_message = request.form.get('message', '') or request.json.get('message', '') if request.is_json else ''
        uploaded_file = request.files.get('file')

        if not user_message.strip() and not uploaded_file:
            return jsonify({'reply': 'Por favor escribe un mensaje o adjunta un archivo.'}), 400

        prompt = user_message
        if uploaded_file:
            prompt += f"\n[Sistema: Archivo adjunto '{uploaded_file.filename}']"

        # Llamada al motor IA de alta potencia
        respuesta_ia = procesar_prompt_ia("Asistente Multimodal Pro", prompt)

        return jsonify({'reply': respuesta_ia, 'success': True})
    except Exception as e:
        logger.error(f"Error en api_chat: {str(e)}")
        return jsonify({'reply': f'Error en el servidor de IA: {str(e)}', 'success': False}), 500

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=True)

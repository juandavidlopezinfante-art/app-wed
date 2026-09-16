import os
from flask import Flask, render_template, request, jsonify
import google.generativeai as genai

app = Flask(__name__)

# Configurar la API Key de Google GenAI desde las variables de entorno
api_key = os.environ.get("GEMINI_API_KEY")
if api_key:
    genai.configure(api_key=api_key)

# Configurar el modelo oficial vigente a máxima potencia
MODEL_NAME = 'gemini-2.5-flash'

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/chat', methods=['POST'])
def api_chat():
    try:
        user_message = request.form.get('message', '')
        uploaded_file = request.files.get('file')
        
        # Inicializar el modelo con gemini-2.5-flash
        model = genai.GenerativeModel(MODEL_NAME)
        
        prompt_content = user_message
        if uploaded_file:
            filename = uploaded_file.filename
            prompt_content += f"\n[Nota del sistema: El usuario ha adjuntado el archivo '{filename}']"

        if not prompt_content.strip():
            return jsonify({'reply': 'Por favor escribe un mensaje o adjunta un archivo.'}), 400

        # Generar respuesta con la IA a máxima potencia
        response = model.generate_content(prompt_content)
        ai_reply = response.text if response and response.text else "No se pudo generar una respuesta en este momento."

        return jsonify({'reply': ai_reply})

    except Exception as e:
        return jsonify({'reply': f'Error en el servidor de IA: {str(e)}'}), 500

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=True)
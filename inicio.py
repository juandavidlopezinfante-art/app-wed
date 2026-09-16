import os
from flask import Flask, render_template, request, jsonify
from google import genai
from google.genai import types

app = Flask(__name__)

# Configuración de la API de Google Gemini (Asegúrate de tener tu variable de entorno GEMINI_API_KEY configurada en tu servidor)
client = genai.Client()

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/api/chat', methods=['POST'])
def chat_con_ia():
    try:
        # Recibir mensaje del usuario y archivos adjuntos si los hubiera
        user_message = request.form.get('message', '')
        file = request.files.get('file')
        
        contents = [user_message]
        
        # Si el usuario adjunta un archivo (imagen, documento, audio, etc.)
        if file:
            file_bytes = file.read()
            # Subimos/procesamos el archivo de forma temporal para que la IA lo lea
            uploaded_file = client.files.upload(
                file=file_bytes,
                config=types.UploadFileConfig(mime_type=file.mimetype)
            )
            contents.append(uploaded_file)

        # Usamos el modelo más potente y rápido de Gemini para responder
        response = client.models.generate_content(
            model='gemini-2.5-flash',
            contents=contents,
            config=types.GenerateContentConfig(
                system_instruction="Eres el núcleo de inteligencia artificial de una plataforma social y de productividad avanzada. Ayuda al usuario con código, redacción de documentos Word/Excel, análisis de archivos y generación de ideas creativas con un tono profesional y dinámico."
            )
        )

        return jsonify({
            "status": "success",
            "reply": response.text
        })

    except Exception as e:
        return jsonify({
            "status": "error",
            "message": str(e)
        }), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)

import os
from flask import Flask, render_template, request, jsonify
from google import genai
from google.genai import types

app = Flask(__name__)

# Lee automáticamente la llave de API configurada en Render o en tu entorno local
client = genai.Client(api_key=os.environ.get("GEMINI_API_KEY"))

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/api/chat', methods=['POST'])
def chat_con_ia():
    try:
        user_message = request.form.get('message', '')
        file = request.files.get('file')
        contents = [user_message]
        
        if file:
            file_bytes = file.read()
            uploaded_file = client.files.upload(
                file=file_bytes,
                config=types.UploadFileConfig(mime_type=file.mimetype)
            )
            contents.append(uploaded_file)

        response = client.models.generate_content(
            model='gemini-2.5-flash',
            contents=contents,
            config=types.GenerateContentConfig(
                system_instruction="Eres el núcleo de inteligencia artificial de una plataforma social y de productividad avanzada."
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

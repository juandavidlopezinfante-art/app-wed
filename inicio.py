import os
import requests
from flask import Flask, render_template, request, jsonify

app = Flask(__name__)

# Configuración de OpenRouter para acceso a IAs de nivel empresarial (Claude 3.5, GPT-4o, etc.)
OPENROUTER_API_KEY = os.environ.get("OPENROUTER_API_KEY")
OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"

# Usaremos un modelo de gama alta por defecto para máxima calidad y profundidad
AI_MODEL = "anthropic/claude-3.5-sonnet" 

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/chat', methods=['POST'])
def api_chat():
    try:
        user_message = request.form.get('message', '')
        uploaded_file = request.files.get('file')
        
        prompt_content = user_message
        if uploaded_file:
            filename = uploaded_file.filename
            prompt_content += f"\n[Sistema: El usuario ha adjuntado el archivo corporativo/técnico '{filename}']"

        if not prompt_content.strip():
            return jsonify({'reply': 'Por favor escribe un mensaje detallado o adjunta un archivo.'}), 400

        if not OPENROUTER_API_KEY:
            return jsonify({'reply': '⚠️ Error crítico: La OPENROUTER_API_KEY no está configurada en las variables de entorno de Render.'}), 500

        # Cabeceras requeridas por OpenRouter para analíticas de la app
        headers = {
            "Authorization": f"Bearer {OPENROUTER_API_KEY}",
            "HTTP-Referer": "https://nexus-ai-pro.onrender.com", 
            "X-Title": "Nexus AI Pro Enterprise",
            "Content-Type": "application/json"
        }

        # Payload con máxima potencia, creatividad y profundidad analítica
        payload = {
            "model": AI_MODEL,
            "messages": [
                {
                    "role": "system",
                    "content": "Eres el núcleo de inteligencia artificial de nivel empresarial de Nexus AI Pro. Ofrece respuestas extremadamente detalladas, profesionales, profundas, creativas y de máxima calidad técnica."
                },
                {
                    "role": "user",
                    "content": prompt_content
                }
            ],
            "temperature": 0.85,
            "max_tokens": 4096
        }

        response = requests.post(OPENROUTER_URL, headers=headers, json=payload, timeout=60)
        
        if response.status_code == 200:
            res_json = response.json()
            ai_reply = res_json['choices'][0]['message']['content']
        else:
            ai_reply = f"Error en el clúster de IA de alto rendimiento (Código {response.status_code}): {response.text}"

        return jsonify({'reply': ai_reply})

    except Exception as e:
        return jsonify({'reply': f'Error crítico de comunicación con el servidor distribuido: {str(e)}'}), 500

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=True)
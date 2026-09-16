import os
import requests
from flask import Flask, render_template, request, jsonify

app = Flask(__name__)

# Configuración del nuevo proveedor de IA de alta potencia (Hugging Face / Router API)
HF_API_KEY = os.environ.get("HF_API_KEY")
API_URL = "https://router.huggingface.co/hf-inference/models/mistralai/Mixtral-8x7B-Instruct-v0.1"

headers = {"Authorization": f"Bearer {HF_API_KEY}"} if HF_API_KEY else {}

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
            prompt_content += f"\n[Sistema: Archivo adjunto '{filename}']"

        if not prompt_content.strip():
            return jsonify({'reply': 'Por favor escribe un mensaje o adjunta un archivo.'}), 400

        # Petición al servidor de IA de alto rendimiento
        payload = {
            "inputs": f"[INST] Actúa como un asistente experto de alta potencia para Nexus AI Pro. Responde con calidad máxima, detalle y precisión a: {prompt_content} [/INST]",
            "parameters": {"max_new_tokens": 1024, "temperature": 0.7, "return_full_text": False}
        }

        response = requests.post(API_URL, headers=headers, json=payload, timeout=30)
        
        if response.status_code == 200:
            res_json = response.json()
            if isinstance(res_json, list) and len(res_json) > 0:
                ai_reply = res_json[0].get('generated_text', 'Respuesta generada con éxito.')
            else:
                ai_reply = str(res_json)
        else:
            ai_reply = f"Error en el servidor de IA de alto rendimiento (Código {response.status_code}): {response.text}"

        return jsonify({'reply': ai_reply})

    except Exception as e:
        return jsonify({'reply': f'Error crítico de conexión con el nuevo servidor: {str(e)}'}), 500

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=True)

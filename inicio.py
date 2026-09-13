from flask import Flask, render_template, request
import requests
import os
import time

app = Flask(__name__)


API_TOKEN = os.environ.get("HUGGINGFACE_TOKEN")
API_URL = "https://api-inference.huggingface.co/models/stabilityai/stable-diffusion-xl-base-1.0"
headers = {"Authorization": f"Bearer {API_TOKEN}"}

# Asegurar carpeta static
os.makedirs('static', exist_ok=True)

@app.route('/')
def home():
    return render_template('index.html', imagen_url=None)

@app.route('/generar', methods=['POST'])
def generar():
    texto_usuario = request.form['prompt']
    
    payload = {"inputs": texto_usuario}
    response = requests.post(API_URL, headers=headers, json=payload)
    
    if response.status_code == 200:
        # Creamos un nombre único basado en el tiempo actual
        nombre_archivo = f"imagen_{int(time.time())}.jpg"
        ruta_imagen = os.path.join('static', nombre_archivo)
        
        with open(ruta_imagen, 'wb') as f:
            f.write(response.content)
            
        return render_template('index.html', imagen_url=nombre_archivo)
    else:
        return f'Error al generar la imagen: {response.text}'

if __name__ == '__main__':
    app.run(debug=True)

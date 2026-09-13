import os
import requests
import base64
from flask import Flask, render_template, request

app = Flask(__name__)

API_TOKEN = os.environ.get("HUGGINGFACE_TOKEN")
API_URL = "https://api-inference.huggingface.co/models/stabilityai/stable-diffusion-2"
headers = {"Authorization": f"Bearer {API_TOKEN}"}

@app.route("/", methods=["GET", "POST"])
def index():
    imagen_base64 = None
    
    if request.method == "POST":
        prompt_usuario = request.form.get("prompt")
        
        if prompt_usuario:
            response = requests.post(API_URL, headers=headers, json={"inputs": prompt_usuario})
            
            if response.status_code == 200:
                encoded_string = base64.b64encode(response.content).decode('utf-8')
                imagen_base64 = f"data:image/jpeg;base64,{encoded_string}"
            else:
                print("Error en Hugging Face:", response.text)
                
    return render_template("index.html", imagen_url=imagen_base64)

if __name__ == "__main__":
    app.run(debug=True)

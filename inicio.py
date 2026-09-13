import os
import base64
import requests
from flask import Flask, render_template, request

app = Flask(__name__)

API_TOKEN = os.environ.get("HUGGINGFACE_TOKEN")
API_URL = "https://api-inference.huggingface.co/models/runwayml/stable-diffusion-v1-5"
headers = {"Authorization": f"Bearer {API_TOKEN}"}

@app.route("/", methods=["GET", "POST"])
def index():
    imagen_base64 = None
    
    if request.method == "POST":
        prompt_usuario = request.form.get("prompt")
        
        if prompt_usuario:
            try:
                response = requests.post(
                    API_URL, 
                    headers=headers, 
                    json={"inputs": prompt_usuario},
                    timeout=60
                )
                
                if response.status_code == 200:
                    encoded_string = base64.b64encode(response.content).decode('utf-8')
                    imagen_base64 = f"data:image/jpeg;base64,{encoded_string}"
                else:
                    print(f"Error API Hugging Face: {response.status_code} - {response.text}")
            except Exception as e:
                print("Excepción al conectar:", str(e))
                
    return render_template("index.html", imagen_url=imagen_base64)

if __name__ == "__main__":
    app.run(debug=True)

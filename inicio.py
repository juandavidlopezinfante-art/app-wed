import os
import base64
import traceback
from flask import Flask, render_template, request
from huggingface_hub import InferenceClient

app = Flask(__name__)

API_TOKEN = os.environ.get("HUGGINGFACE_TOKEN")
client = InferenceClient(token=API_TOKEN)

@app.route("/", methods=["GET", "POST"])
def index():
    imagen_base64 = None
    
    if request.method == "POST":
        prompt_usuario = request.form.get("prompt")
        
        if prompt_usuario:
            try:
                image = client.text_to_image(
                    prompt_usuario,
                    model="runwayml/stable-diffusion-v1-5"
                )
                
                import io
                buffered = io.BytesIO()
                image.save(buffered, format="JPEG")
                encoded_string = base64.b64encode(buffered.getvalue()).decode('utf-8')
                imagen_base64 = f"data:image/jpeg;base64,{encoded_string}"
            except Exception as e:
                print("--- ERROR DETALLADO ---")
                traceback.print_exc()
                
    return render_template("index.html", imagen_url=imagen_base64)

if __name__ == "__main__":
    app.run(debug=True)

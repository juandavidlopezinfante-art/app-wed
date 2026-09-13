import os
from flask import Flask, render_template, request

app = Flask(__name__)

@app.route("/", methods=["GET", "POST"])
def index():
    imagen_url = None
    
    if request.method == "POST":
        prompt_usuario = request.form.get("prompt")
        
        if prompt_usuario:
            # Reemplazamos los espacios del prompt con %20 para que la URL sea válida
            prompt_formateado = prompt_usuario.replace(" ", "%20")
            # Generamos la URL directa de la imagen
            imagen_url = f"https://image.pollinations.ai/prompt/{prompt_formateado}"
                
    return render_template("index.html", imagen_url=imagen_url)

if __name__ == "__main__":
    app.run(debug=True)

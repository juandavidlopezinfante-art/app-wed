import os
from flask import Flask, render_template, request

app = Flask(__name__)

@app.route("/", methods=["GET", "POST"])
def index():
    imagen_url = None
    
    if request.method == "POST":
        prompt_usuario = request.form.get("prompt")
        estilo = request.form.get("estilo")
        
        if prompt_usuario:
            # Añadimos modificadores automáticos según el estilo elegido para mejorar la calidad
            if estilo == "anime":
                prompt_completo = f"{prompt_usuario}, high quality anime style, detailed digital art, vibrant colors"
            elif estilo == "realista":
                prompt_completo = f"{prompt_usuario}, photorealistic, hyperrealistic, 8k resolution, cinematic lighting, highly detailed photograph"
            elif estilo == "3d":
                prompt_completo = f"{prompt_usuario}, 3d render, blender style, octane render, unreal engine 5, smooth textures"
            else:
                prompt_completo = prompt_usuario
                
            prompt_formateado = prompt_completo.replace(" ", "%20")
            imagen_url = f"https://image.pollinations.ai/prompt/{prompt_formateado}"
                
    return render_template("index.html", imagen_url=imagen_url)

if __name__ == "__main__":
    app.run(debug=True)

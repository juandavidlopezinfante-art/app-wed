import os
import random
import base64
from flask import Flask, render_template, request

app = Flask(__name__)

@app.route("/", methods=["GET", "POST"])
def index():
    imagen_url = None
    imagen_usuario_base64 = None
    
    if request.method == "POST":
        prompt_usuario = request.form.get("prompt")
        estilo = request.form.get("estilo")
        
        # 1. Procesar si el usuario subió una imagen
        archivo = request.files.get("imagen_subida")
        if archivo and archivo.filename != '':
            encoded_string = base64.b64encode(archivo.read()).decode('utf-8')
            imagen_usuario_base64 = f"data:image/jpeg;base64,{encoded_string}"
            if not prompt_usuario:
                prompt_usuario = "High quality enhancement of the uploaded photo"

        # 2. Inteligencia de Prompts y Estilos (Mejora radical de calidad)
        if prompt_usuario:
            # Optimizamos los modificadores según el estilo elegido para que la IA nunca falle
            if estilo == "anime":
                prompt_completo = f"{prompt_usuario}, masterpiece, high quality anime style, studio trigger or ufotable style, detailed line art, vibrant cinematic colors, 4k"
            elif estilo == "realista":
                prompt_completo = f"{prompt_usuario}, ultra realistic photography, 8k resolution, shot on 35mm lens, hyperdetailed skin texture, dramatic cinematic lighting, photorealistic"
            elif estilo == "3d":
                prompt_completo = f"{prompt_usuario}, 3d character render, blender cycles, octane render, unreal engine 5, clay render, smooth lighting, volumetric effects"
            else:
                prompt_completo = f"{prompt_usuario}, highly detailed, professional digital painting"
                
            prompt_formateado = prompt_completo.replace(" ", "%20")
            
            # Generamos un número aleatorio único para evitar caché y garantizar variedad
            seed_aleatorio = random.randint(1, 99999999)
            
            # Usamos parámetros avanzados de la API para asegurar máxima nitidez
            imagen_url = f"https://image.pollinations.ai/prompt/{prompt_formateado}?seed={seed_aleatorio}&width=768&height=768&nologo=true&enhance=true"
                
    return render_template("index.html", imagen_url=imagen_url, imagen_usuario=imagen_usuario_base64)

if __name__ == "__main__":
    app.run(debug=True)

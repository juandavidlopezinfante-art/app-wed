from flask import Flask, render_template, request, redirect, url_for
import os

app = Flask(__name__)

# Carpeta temporal para guardar lo que el usuario suba
UPLOAD_FOLDER = 'static/uploads'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

@app.route("/", methods=["GET", "POST"])
def index():
    resultado_url = None
    es_video = False
    resolucion_elegida = "hd"

    if request.method == "POST":
        prompt = request.form.get("prompt")
        tipo_salida = request.form.get("tipo_salida") # 'imagen' o 'video'
        resolucion = request.form.get("resolucion") # 'hd', 'fhd', '4k'
        estilo = request.form.get("estilo")
        
        resolucion_elegida = resolucion

        # Manejo del archivo subido (imagen o video de referencia)
        if "archivo_referencia" in request.files:
            archivo = request.files["archivo_referencia"]
            if archivo.filename != "":
                ruta_archivo = os.path.join(app.config['UPLOAD_FOLDER'], archivo.filename)
                archivo.save(ruta_archivo)
                # Aquí puedes usar 'ruta_archivo' para enviarla a tu API de IA si requiere referencia

        # Lógica según lo que el usuario pidió generar
        if tipo_salida == "video":
            es_video = True
            # AQUÍ CONECTAS TU API DE VIDEOS (Ej: Replicate, Runway, etc.)
            # Puedes ajustar los parámetros de resolución según 'resolucion' (HD, 4K)
            print(f"Generando video en {resolucion} con estilo {estilo} para el prompt: {prompt}")
            
            # URL de ejemplo de video generado
            resultado_url = "https://www.w3schools.com/html/mov_bbb.mp4"
        else:
            es_video = False
            # AQUÍ TU LÓGICA ACTUAL DE IMÁGENES
            print(f"Generando imagen en {resolucion} con estilo {estilo} para el prompt: {prompt}")
            
            # URL de ejemplo de imagen generada
            resultado_url = "https://picsum.photos/800/450"

    return render_template(
        "index.html", 
        resultado_url=resultado_url, 
        es_video=es_video, 
        resolucion_elegida=resolucion_elegida
    )

if __name__ == "__main__":
    app.run(debug=True)

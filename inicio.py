from flask import Flask, render_template, request, send_from_directory
import os
import openpyxl

app = Flask(__name__)

# Carpeta para guardar los archivos generados
UPLOAD_FOLDER = 'static/uploads'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

@app.route("/", methods=["GET", "POST"])
def index():
    resultado_url = None
    es_video = False
    tipo_generado = None

    if request.method == "POST":
        prompt = request.form.get("prompt")
        tipo_salida = request.form.get("tipo_salida")
        
        if tipo_salida == "excel":
            tipo_generado = "excel"
            
            # Creamos el archivo de Excel profesional con openpyxl
            wb = openpyxl.Workbook()
            ws = wb.active
            ws.title = "Reporte Ejecutivo"
            
            # Estilos básicos simulando datos empresariales basados en el prompt del usuario
            ws['A1'] = "REPORTE EMPRESARIAL GENERADO POR IA"
            ws['A3'] = "Concepto / Descripción"
            ws['B3'] = "Detalle del Prompt"
            ws['C3'] = "Estado"
            
            ws['A4'] = prompt
            ws['B4'] = "Datos procesados y optimizados"
            ws['C4'] = "Completado"
            
            # Guardamos el archivo en la carpeta de subidas estáticas
            nombre_archivo = "reporte_empresarial.xlsx"
            ruta_excel = os.path.join(app.config['UPLOAD_FOLDER'], nombre_archivo)
            wb.save(ruta_excel)
            
            # URL de descarga para la plantilla
            resultado_url = f"/static/uploads/{nombre_archivo}"

        elif tipo_salida == "video":
            tipo_generado = "video"
            es_video = True
            resultado_url = "https://www.w3schools.com/html/mov_bbb.mp4"
        else:
            tipo_generado = "imagen"
            es_video = False
            resultado_url = "https://picsum.photos/800/450"

    return render_template(
        "index.html", 
        resultado_url=resultado_url, 
        es_video=es_video, 
        tipo_generado=tipo_generado
    )

if __name__ == "__main__":
    app.run(debug=True)

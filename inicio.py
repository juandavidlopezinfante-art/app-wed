from flask import Flask, render_template, request
import os
import openpyxl

app = Flask(__name__)

UPLOAD_FOLDER = 'static/uploads'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

@app.route("/", methods=["GET", "POST"])
def index():
    resultado_url = None
    es_video = False
    tipo_generado = None

    if request.method == "POST":
        # Capturar el prompt y pasarlo a minúsculas para entender jerga, modismos y lenguaje informal
        prompt = request.form.get("prompt", "")
        prompt_lower = prompt.lower()
        
        # --- FILTRO INTELIGENTE DE LENGUAJE NATURAL ---
        # Analiza la frase del usuario y decide automáticamente qué herramienta usar
        if any(palabra in prompt_lower for palabra in ["excel", "tabla", "reporte", "cuentas", "datos", "inventario", "ventas", "listado", "tablita"]):
            tipo_salida = "excel"
        elif any(palabra in prompt_lower for palabra in ["video", "animacion", "movimiento", "gif", "videito", "clip", "grabar"]):
            tipo_salida = "video"
        else:
            tipo_salida = "imagen" # Interpreta cualquier otro término como solicitud visual
        
        # Lógica de procesamiento según la intención detectada
        if tipo_salida == "excel":
            tipo_generado = "excel"
            wb = openpyxl.Workbook()
            ws = wb.active
            ws.title = "Reporte Inteligente"
            
            ws['A1'] = "REPORTE EMPRESARIAL AUTOMATIZADO"
            ws['A3'] = "Petición del Usuario"
            ws['B3'] = "Análisis de Intención"
            ws['C3'] = "Estado"
            
            ws['A4'] = prompt
            ws['B4'] = "Procesado mediante lenguaje natural"
            ws['C4'] = "Exitoso"
            
            nombre_archivo = "reporte_inteligente.xlsx"
            ruta_excel = os.path.join(app.config['UPLOAD_FOLDER'], nombre_archivo)
            wb.save(ruta_excel)
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

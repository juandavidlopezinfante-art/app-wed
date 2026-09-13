from flask import Flask, render_template, request
import os
import openpyxl
import docx

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
        prompt = request.form.get("prompt", "")
        prompt_lower = prompt.lower()
        tipo_salida = request.form.get("tipo_salida")
        
        # Revisar si el usuario subió un archivo para modificar o usar como referencia
        archivo_subido = request.files.get("archivo_referencia")
        nombre_archivo_subido = archivo_subido.filename if archivo_subido else ""

        # --- DETECCIÓN AUTOMÁTICA DE INTENCIÓN ---
        if tipo_salida == "auto":
            if nombre_archivo_subido.endswith('.docx') or any(p in prompt_lower for p in ["word", "documento", "texto", "carta", "oficio"]):
                tipo_salida = "word"
            elif nombre_archivo_subido.endswith('.xlsx') or any(palabra in prompt_lower for palabra in ["excel", "tabla", "reporte", "cuentas", "datos", "inventario", "ventas"]):
                tipo_salida = "excel"
            elif any(palabra in prompt_lower for palabra in ["video", "animacion", "movimiento", "gif", "videito", "clip"]):
                tipo_salida = "video"
            else:
                tipo_salida = "imagen"

        # --- PROCESAMIENTO SEGÚN EL TIPO ---
        if tipo_salida == "word":
            tipo_generado = "word"
            
            # Si el usuario subió un Word existente, lo leemos y modificamos
            if nombre_archivo_subido.endswith('.docx'):
                ruta_entrada = os.path.join(app.config['UPLOAD_FOLDER'], nombre_archivo_subido)
                archivo_subido.save(ruta_entrada)
                
                doc = docx.Document(ruta_entrada)
                doc.add_paragraph(f"\n[Actualización por IA]: {prompt}")
                
                nombre_salida = "documento_modificado.docx"
                ruta_salida = os.path.join(app.config['UPLOAD_FOLDER'], nombre_salida)
                doc.save(ruta_salida)
                resultado_url = f"/static/uploads/{nombre_salida}"
            else:
                # Si no subió ninguno pero pidió un Word, creamos uno nuevo desde cero
                doc = docx.Document()
                doc.add_heading('Documento Generado por IA', 0)
                doc.add_paragraph(f"Petición: {prompt}")
                
                nombre_salida = "nuevo_documento.docx"
                ruta_salida = os.path.join(app.config['UPLOAD_FOLDER'], nombre_salida)
                doc.save(ruta_salida)
                resultado_url = f"/static/uploads/{nombre_salida}"

        elif tipo_salida == "excel":
            tipo_generado = "excel"
            wb = openpyxl.Workbook()
            ws = wb.active
            ws.title = "Reporte Inteligente"
            
            ws['A1'] = "REPORTE EMPRESARIAL AUTOMATIZADO"
            ws['A3'] = "Petición del Usuario"
            ws['B3'] = "Análisis del Sistema"
            ws['C3'] = "Estado"
            
            ws['A4'] = prompt
            ws['B4'] = "Modificado mediante documento de referencia" if nombre_archivo_subido else "Creado desde cero"
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

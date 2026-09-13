from flask import Flask, render_template, request
import os
import openpyxl
import docx
from PIL import Image
import pytesseract
from pypdf import PdfReader

app = Flask(__name__)

UPLOAD_FOLDER = 'static/uploads'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

@app.route("/", methods=["GET", "POST"])
def index():
    resultado_url = None
    es_video = False
    tipo_generado = None
    texto_extraido = ""

    if request.method == "POST":
        accion = request.form.get("accion")
        
        # --- CASO 1: EXTRACTOR OCR ---
        if accion == "ocr":
            archivo_ocr = request.files.get("archivo_ocr")
            if archivo_ocr and archivo_ocr.filename != "":
                ruta_imagen = os.path.join(app.config['UPLOAD_FOLDER'], archivo_ocr.filename)
                archivo_ocr.save(ruta_imagen)
                
                try:
                    imagen = Image.open(ruta_imagen)
                    texto_extraido = pytesseract.image_to_string(imagen)
                    if not texto_extraido.strip():
                        texto_extraido = "No se detectó texto claro en la imagen."
                except Exception as e:
                    texto_extraido = f"Error: {str(e)}"

                wb = openpyxl.Workbook()
                ws = wb.active
                ws.title = "Datos OCR"
                ws['A1'] = "REPORTE OCR"
                ws['A3'] = "Texto Detectado"
                
                lineas = texto_extraido.split('\n')
                fila = 4
                for linea in lineas:
                    if linea.strip():
                        ws[f'A{fila}'] = linea.strip()
                        fila += 1

                nombre_excel = "reporte_ocr.xlsx"
                ruta_excel = os.path.join(app.config['UPLOAD_FOLDER'], nombre_excel)
                wb.save(ruta_excel)
                tipo_generado = "ocr"
                resultado_url = f"/static/uploads/{nombre_excel}"

        # --- CASO 2: LECTOR Y PROCESADOR DE PDF ---
        elif accion == "pdf":
            archivo_pdf = request.files.get("archivo_pdf")
            if archivo_pdf and archivo_pdf.filename != "":
                ruta_pdf = os.path.join(app.config['UPLOAD_FOLDER'], archivo_pdf.filename)
                archivo_pdf.save(ruta_pdf)
                
                try:
                    lector = PdfReader(ruta_pdf)
                    texto_extraido = ""
                    for pagina in lector.pages:
                        extraido = pagina.extract_text()
                        if extraido:
                            texto_extraido += extraido + "\n"
                    
                    if not texto_extraido.strip():
                        texto_extraido = "El PDF no contiene texto seleccionable (puede ser una imagen escaneada)."
                except Exception as e:
                    texto_extraido = f"Error al leer el PDF: {str(e)}"

                # Crear un documento Word limpio con el contenido del PDF
                doc = docx.Document()
                doc.add_heading('Resumen de Documento PDF', 0)
                doc.add_paragraph("Contenido extraído automáticamente:")
                for bloque in texto_extraido.split('\n\n'):
                    if bloque.strip():
                        doc.add_paragraph(bloque.strip())

                nombre_word = "resumen_pdf.docx"
                ruta_word = os.path.join(app.config['UPLOAD_FOLDER'], nombre_word)
                doc.save(ruta_word)
                tipo_generado = "pdf_resumen"
                resultado_url = f"/static/uploads/{nombre_word}"

        # --- CASO 3: GENERADOR CREATIVO ---
        elif accion == "creativo":
            prompt = request.form.get("prompt", "")
            prompt_lower = prompt.lower()
            tipo_salida = request.form.get("tipo_salida")
            
            archivo_subido = request.files.get("archivo_referencia")
            nombre_archivo_subido = archivo_subido.filename if archivo_subido else ""

            if tipo_salida == "auto":
                if nombre_archivo_subido.endswith('.docx') or any(p in prompt_lower for p in ["word", "documento", "texto"]):
                    tipo_salida = "word"
                elif nombre_archivo_subido.endswith('.xlsx') or any(p in prompt_lower for p in ["excel", "tabla", "reporte", "datos", "ventas"]):
                    tipo_salida = "excel"
                elif any(p in prompt_lower for p in ["video", "animacion", "movimiento", "gif"]):
                    tipo_salida = "video"
                else:
                    tipo_salida = "imagen"

            if tipo_salida == "word":
                tipo_generado = "word"
                if nombre_archivo_subido.endswith('.docx'):
                    ruta_entrada = os.path.join(app.config['UPLOAD_FOLDER'], nombre_archivo_subido)
                    archivo_subido.save(ruta_entrada)
                    doc = docx.Document(ruta_entrada)
                    doc.add_paragraph(f"\n[Actualización]: {prompt}")
                else:
                    doc = docx.Document()
                    doc.add_heading('Documento Generado', 0)
                    doc.add_paragraph(f"Petición: {prompt}")
                
                nombre_salida = "documento_editado.docx"
                ruta_salida = os.path.join(app.config['UPLOAD_FOLDER'], nombre_salida)
                doc.save(ruta_salida)
                resultado_url = f"/static/uploads/{nombre_salida}"

            elif tipo_salida == "excel":
                tipo_generado = "excel"
                wb = openpyxl.Workbook()
                ws = wb.active
                ws['A1'] = "REPORTE EMPRESARIAL"
                ws['A3'] = "Prompt"
                ws['B3'] = "Detalle"
                ws['A4'] = prompt
                ws['B4'] = "Procesado correctamente"
                
                nombre_excel = "reporte_creativo.xlsx"
                ruta_excel = os.path.join(app.config['UPLOAD_FOLDER'], nombre_excel)
                wb.save(ruta_excel)
                resultado_url = f"/static/uploads/{nombre_excel}"

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
        tipo_generado=tipo_generado,
        texto_extraido=texto_extraido
    )

if __name__ == "__main__":
    app.run(debug=True)

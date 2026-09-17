from pathlib import Path

archivos_html = [
    Path("templates/index.html"),
    Path("templates/dashboard.html"),
]

for archivo in archivos_html:
    if archivo.exists():
        contenido = archivo.read_text(encoding="utf-8")
        # Limpia caracteres invisibles de comillas invertidas
        contenido = contenido.replace("\u2060", "")
        archivo.write_text(contenido, encoding="utf-8")

archivo_optimizado = Path("inicio_optimized.py")
if archivo_optimizado.exists():
    contenido = archivo_optimizado.read_text(encoding="utf-8")
    lineas = contenido.splitlines()
    if lineas and lineas[0].strip() == "```python":
        lineas = lineas[1:]
    if lineas and lineas[-1].strip() == "```":
        lineas = lineas[:-1]
    archivo_optimizado.write_text("\n".join(lineas) + "\n", encoding="utf-8")

print("Archivos limpiados correctamente.")
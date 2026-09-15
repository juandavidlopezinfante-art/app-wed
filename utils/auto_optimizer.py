import os
import google.generativeai as genai

# Configurar API de Gemini
api_key = os.environ.get("GEMINI_API_KEY")
if api_key:
    genai.configure(api_key=api_key)

def optimize_code_module(file_path):
    """
    Lee un archivo de código fuente del proyecto, lo analiza con Gemini 
    para detectar fallas o ineficiencias y genera una versión optimizada.
    """
    if not os.path.exists(file_path):
        return f"El archivo {file_path} no existe."

    with open(file_path, 'r', encoding='utf-8') as f:
        source_code = f.read()

    model = genai.GenerativeModel('gemini-3.8-flash')
    
    prompt = (
        "Eres un arquitecto de software autónomo de nivel senior trabajando para 'Digital Business IA'. "
        "Analiza el siguiente código fuente en Python, detecta posibles cuellos de botella, "
        "mejora su rendimiento, asegura que maneje excepciones correctamente y "
        "devuelve ÚNICAMENTE el código mejorado y limpio, listo para producción:\n\n"
        f"{source_code}"
    )

    response = model.generate_content(prompt)
    
    # Guardar una copia optimizada del archivo
    optimized_path = file_path.replace('.py', '_optimized.py')
    with open(optimized_path, 'w', encoding='utf-8') as f:
        f.write(response.text)
        
    return f"Optimización completada. Archivo generado: {optimized_path}"

if __name__ == "__main__":
    # Ejemplo de auto-optimización sobre tu archivo principal del servidor
    resultado = optimize_code_module("inicio.py")
    print(resultado)

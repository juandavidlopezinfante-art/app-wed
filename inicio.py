import os
from flask import Flask, render_template, request, jsonify
import google.generativeai as genai

app = Flask(__name__)

# Configurar la API de Gemini con la variable de entorno segura de Render
api_key = os.environ.get("GEMINI_API_KEY")
if api_key:
    genai.configure(api_key=api_key)

# Configuración de precisión estricta (Temperatura 0.0 para eliminar alucinaciones)
generation_config = {
    "temperature": 0.0,
}

# Instrucciones de sistema corporativas de tolerancia cero
system_instruction = (
    "Eres el motor central de 'Digital Business IA'. "
    "Operas bajo un entorno estrictamente determinista y profesional. "
    "No inventes datos, no alucines información y responde con total precisión analítica "
    "basándote exclusivamente en las instrucciones y datos proporcionados por el usuario."
)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/dashboard')
def dashboard():
    return render_template('dashboard.html')

@app.route('/api/generate', methods=['POST'])
def api_generate():
    try:
        data = request.get_json()
        tool_name = data.get('toolName', 'Asistente General')
        prompt = data.get('prompt', '')

        if not prompt:
            return jsonify({"error": "⚠️ Por favor ingresa una instrucción válida."}), 400

        # Cargar el modelo con el procesador gemini-1.5-flash y parámetros de cero error
        model = genai.GenerativeModel(
            model_name='gemini-1.5-flash',
            generation_config=generation_config,
            system_instruction=system_instruction
        )

        # Estructurar la entrada con contexto de la herramienta
        full_context_prompt = f"Módulo activo: {tool_name}\nSolicitud del usuario: {prompt}"

        response = model.generate_content(full_context_prompt)

        return jsonify({"response": response.text})

    except Exception as e:
        return jsonify({"error": f"❌ Error interno en el servidor al conectar con Gemini: {str(e)}"}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)

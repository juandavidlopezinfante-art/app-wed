import os
import logging
import requests
from flask import Flask, request, jsonify, render_template

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
logger = logging.getLogger("DigitalBusinessIA-Cluster")

app = Flask(__name__)

# Llaves de los diferentes servidores
OPENROUTER_API_KEY = os.environ.get("OPENROUTER_API_KEY")
GROQ_API_KEY = os.environ.get("GROQ_API_KEY")
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/health', methods=['GET'])
def health():
    return jsonify({"status": "cluster-online"}), 200

@app.route('/api/generate', methods=['POST'])
def api_generate():
    try:
        data = request.get_json(silent=True) or {}
        tool_name = data.get('toolName', 'Asistente IA').strip()
        prompt = data.get('prompt', '').strip()

        if not prompt:
            return jsonify({"error": "El prompt está vacío."}), 400

        system_prompt = f"Eres un experto profesional nivel senior en {tool_name}. Proporciona respuestas impecables, analíticas y de alto valor comercial."
        texto_generado = None

        # -------------------------------------------------------------
        # SERVIDOR 1: OpenRouter (Modelo de alto rendimiento)
        # -------------------------------------------------------------
        if OPENROUTER_API_KEY and not texto_generado:
            try:
                headers = {
                    "Authorization": f"Bearer {OPENROUTER_API_KEY}",
                    "HTTP-Referer": "https://app-wed.onrender.com",
                    "X-Title": "Digital Business IA Pro",
                    "Content-Type": "application/json"
                }
                payload = {
                    "model": "google/gemini-flash-1.5",
                    "messages": [
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": prompt}
                    ]
                }
                response = requests.post("https://openrouter.ai/api/v1/chat/completions", headers=headers, json=payload, timeout=20)
                if response.status_code == 200:
                    res_json = response.json()
                    texto_generado = res_json.get("choices", [{}])[0].get("message", {}).get("content")
                    logger.info("Respuesta generada exitosamente vía OpenRouter.")
            except Exception as e:
                logger.warning(f"OpenRouter falló, pasando al siguiente servidor: {e}")

        # -------------------------------------------------------------
        # SERVIDOR 2: Groq API (Ultra velocidad con Llama 3.3)
        # -------------------------------------------------------------
        if GROQ_API_KEY and not texto_generado:
            try:
                headers = {
                    "Authorization": f"Bearer {GROQ_API_KEY}",
                    "Content-Type": "application/json"
                }
                payload = {
                    "model": "llama-3.3-70b-versatile",
                    "messages": [
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": prompt}
                    ]
                }
                response = requests.post("https://api.groq.com/openai/v1/chat/completions", headers=headers, json=payload, timeout=20)
                if response.status_code == 200:
                    res_json = response.json()
                    texto_generado = res_json.get("choices", [{}])[0].get("message", {}).get("content")
                    logger.info("Respuesta generada exitosamente vía Groq API.")
            except Exception as e:
                logger.warning(f"Groq falló, pasando al siguiente servidor: {e}")

        # Si ningún servidor respondió
        if not texto_generado:
            return jsonify({"error": "Todos los servidores del clúster están ocupados o faltan configurar llaves adicionales en Render."}), 500

        return jsonify({"response": texto_generado, "success": True})

    except Exception as e:
        logger.exception("Error crítico en el clúster de IA:")
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)

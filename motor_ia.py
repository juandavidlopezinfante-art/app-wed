import os
import logging
import urllib.parse
import google.generativeai as genai

logger = logging.getLogger("DigitalBusinessIA-Motor")

API_KEYS_POOL = [
    os.environ.get("GEMINI_CHAT_KEY"),
    os.environ.get("GEMINI_CHAT_KEY_1"),
    os.environ.get("GEMINI_CHAT_KEY_2"),
    os.environ.get("GEMINI_API_KEY"),
    os.environ.get("GEMINI_FEED_KEY"),
    os.environ.get("UNRESTRICTED_API_KEY")
]
API_KEYS_POOL = [key.strip() for key in API_KEYS_POOL if key and key.strip()]
PRIMARY_API_KEY = API_KEYS_POOL[0] if API_KEYS_POOL else None

if PRIMARY_API_KEY:
    genai.configure(api_key=PRIMARY_API_KEY)

generation_config = {
    "temperature": 0.9,
    "top_p": 0.95,
    "top_k": 40,
    "max_output_tokens": 8192,
}

def obtener_motor_inteligente():
    """Selecciona aleatoriamente una llave del pool y usa el modelo oficial vigente."""
    if API_KEYS_POOL:
        import random
        genai.configure(api_key=random.choice(API_KEYS_POOL))
    
    # Usamos estrictamente el modelo actual exigido por la API de Google
    modelos_disponibles = ['gemini-3.6-flash', 'gemini-pro']
    for nombre_modelo in modelos_disponibles:
        try:
            return genai.GenerativeModel(nombre_modelo, generation_config=generation_config)
        except Exception:
            continue
    return genai.GenerativeModel('gemini-pro', generation_config=generation_config)

def procesar_prompt_ia(tool_name, prompt):
    """Ejecuta la consulta con Gemini de forma ultra segura."""
    try:
        if not API_KEYS_POOL:
            return "⚠️ Error: Faltan las API Keys de Gemini configuradas en el servidor de Render."
        
        model = obtener_motor_inteligente()
        prompt_completo = f"Actúa como un experto profesional en {tool_name}. Responde de forma detallada, creativa y estructurada:\n\n{prompt}"
        
        chat_response = model.generate_content(prompt_completo)
        
        if hasattr(chat_response, 'text') and chat_response.text:
            return chat_response.text
        elif chat_response.candidates:
            return chat_response.candidates[0].content.parts[0].text
        else:
            return "Respuesta generada con éxito por el clúster."
    except Exception as e:
        logger.error(f"Error crítico en motor IA: {str(e)}")
        return f"⚠️ Error interno procesando la solicitud: {str(e)}"

def generar_url_imagen(prompt, is_adult=False):
    """Genera URLs dinámicas de alta calidad."""
    if is_adult:
        encoded_prompt = urllib.parse.quote(prompt + ", highly detailed digital art, uncensored concept art, expressive character design")
    else:
        encoded_prompt = urllib.parse.quote(prompt)

    return f"https://image.pollinations.ai/prompt/{encoded_prompt}?width=1024&height=1024&nologo=true"

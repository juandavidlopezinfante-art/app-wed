import os
from pathlib import Path
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent
load_dotenv(BASE_DIR / ".env")

class Config:
    SECRET_KEY = os.getenv("SECRET_KEY", "change_me_to_a_long_secret")
    DB_NAME = os.getenv("DB_NAME", "ecosistema_privado.db")
    OPENROUTER_API_KEY = (os.getenv("OPENROUTER_API_KEY") or "").strip()
    OPENROUTER_MODEL = os.getenv("OPENROUTER_MODEL", "google/gemini-flash-1.5")
    OPENROUTER_URL = os.getenv(
        "OPENROUTER_URL",
        "https://openrouter.ai/api/v1/chat/completions",
    )
    APP_URL = os.getenv("APP_URL", "http://localhost:5000")
    OPENROUTER_TIMEOUT = float(os.getenv("OPENROUTER_TIMEOUT", "35"))
    OPENROUTER_MAX_TOKENS = int(os.getenv("OPENROUTER_MAX_TOKENS", "1500"))
    MAX_PROMPT_LENGTH = int(os.getenv("MAX_PROMPT_LENGTH", "12000"))
    LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")

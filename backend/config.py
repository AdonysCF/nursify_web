import os
from dotenv import load_dotenv

load_dotenv()

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
DATABASE_URL = "sqlite:///./storage/app.db"

# Puedes cambiarlo aquí o en tu .env por: "gemini-2.5-flash", "gemini-1.5-pro", etc.
MODELO_GEMINI = os.getenv("GEMINI_MODEL", "gemini-3.5-flash")
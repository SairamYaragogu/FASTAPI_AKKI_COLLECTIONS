import os
from dotenv import load_dotenv

# Load environment variables from .env file if available
load_dotenv()

DB_HOST = os.getenv("DB_HOST", "localhost")
DB_USER = os.getenv("DB_USER", "root")
DB_PASSWORD = os.getenv("DB_PASSWORD", "Sairam.4114")
DB_NAME = os.getenv("DB_NAME", "akki_collections_db")
DB_PORT = int(os.getenv("DB_PORT", "3306"))

ADMIN_USERNAME = os.getenv("ADMIN_USERNAME", "admin")
ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD", "admin123")

FASTAPI_HOST = os.getenv("FASTAPI_HOST", "127.0.0.1")
FASTAPI_PORT = int(os.getenv("FASTAPI_PORT", "8000"))
BACKEND_URL = f"http://{FASTAPI_HOST}:{FASTAPI_PORT}"

# OpenAI and RAG Configurations
# You can paste your paid OpenAI API Key directly below (e.g. "sk-proj-...") or set it in .env:
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "text-embedding-3-small")

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
POLICIES_DIR = os.path.join(BASE_DIR, "data", "policies")
VECTOR_CACHE_PATH = os.path.join(BASE_DIR, "data", "policies_index.pkl")

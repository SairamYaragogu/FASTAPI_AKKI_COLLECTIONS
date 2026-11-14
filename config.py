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

# Advanced RAG & OpenAI Configurations
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4.1-mini")
CHAT_MODEL = os.getenv("CHAT_MODEL", OPENAI_MODEL)
EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "text-embedding-3-small")
DATA_FOLDER = os.getenv("DATA_FOLDER", "data/documents")
CHROMA_FOLDER = os.getenv("CHROMA_FOLDER", "chroma_db")
COLLECTION_NAME = os.getenv("COLLECTION_NAME", "akki_advanced_rag")

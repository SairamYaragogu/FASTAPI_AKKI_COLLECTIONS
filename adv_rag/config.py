# Add your OpenAI API key here for this beginner demo.
# Do not upload this file with a real API key to GitHub.
import os

from dotenv import load_dotenv

load_dotenv()

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
CHAT_MODEL = os.getenv("CHAT_MODEL") or os.getenv("OPENAI_MODEL") or "gpt-4.1-mini"
EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "text-embedding-3-small")

_data_folder = os.getenv("DATA_FOLDER", "data/documents")
DATA_FOLDER = _data_folder if os.path.isabs(_data_folder) else os.path.join(PROJECT_ROOT, _data_folder)

_chroma_folder = os.getenv("CHROMA_FOLDER", "chroma_db")
CHROMA_FOLDER = _chroma_folder if os.path.isabs(_chroma_folder) else os.path.join(PROJECT_ROOT, _chroma_folder)

COLLECTION_NAME = os.getenv("COLLECTION_NAME", "akki_advanced_rag")



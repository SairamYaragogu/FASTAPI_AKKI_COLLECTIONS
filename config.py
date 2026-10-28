import os

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

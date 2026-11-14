import os
try:
    from .config import DATA_FOLDER
except (ImportError, ValueError):
    from config import DATA_FOLDER

def load_documents():
    """Read every TXT file from the data folder."""
    documents = []

    if not os.path.exists(DATA_FOLDER):
        return documents

    for filename in os.listdir(DATA_FOLDER):
        if filename.endswith(".txt"):
            path = os.path.join(DATA_FOLDER, filename)

            with open(path, "r", encoding="utf-8") as file:
                documents.append({
                    "source": filename,
                    "text": file.read()
                })

    return documents
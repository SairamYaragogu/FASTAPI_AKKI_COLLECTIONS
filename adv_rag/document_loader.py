import os
try:
    from .config import DATA_FOLDER
except (ImportError, ValueError):
    from config import DATA_FOLDER

def load_documents(verbose=True):
    """Read every TXT file from the data folder and log retrieval details."""
    documents = []

    if verbose:
        print("\n" + "=" * 80)
        print("📁 [ADV RAG | STEP 1: DOCUMENT RETRIEVAL & LOADING]")
        print("=" * 80)
        print(f"   📂 Target Folder: {os.path.abspath(DATA_FOLDER)}")

    if not os.path.exists(DATA_FOLDER):
        if verbose:
            print(f"   ❌ Folder '{DATA_FOLDER}' does not exist!")
        return documents

    txt_files = [f for f in sorted(os.listdir(DATA_FOLDER)) if f.endswith(".txt")]
    if verbose:
        print(f"   📄 Discovered {len(txt_files)} text document file(s) for ingestion:")

    total_bytes = 0
    for idx, filename in enumerate(txt_files, 1):
        path = os.path.join(DATA_FOLDER, filename)
        file_size = os.path.getsize(path)
        total_bytes += file_size

        with open(path, "r", encoding="utf-8") as file:
            content = file.read()
            documents.append({
                "source": filename,
                "text": content,
                "size_bytes": file_size,
                "char_count": len(content)
            })
            if verbose:
                print(f"   [{idx}/{len(txt_files)}] Retrieved: '{filename}' | Size: {file_size:,} bytes | Chars: {len(content):,} chars")

    if verbose:
        print(f"   ✅ Loading Finished: Successfully loaded {len(documents)} document(s) ({total_bytes:,} total bytes).")
        print("=" * 80 + "\n")

    return documents
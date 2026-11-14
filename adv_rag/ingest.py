try:
    from .document_loader import load_documents
    from .chunking import create_chunks
    from .openai_service import create_embeddings
    from .chroma_store import add_chunks, clear_database
except (ImportError, ValueError):
    from document_loader import load_documents
    from chunking import create_chunks
    from openai_service import create_embeddings
    from chroma_store import add_chunks, clear_database

def ingest_documents():
    """Complete document ingestion workflow."""
    documents = load_documents()
    chunks = create_chunks(documents)

    # Generate embeddings once during ingestion.
    texts = [chunk["text"] for chunk in chunks]
    embeddings = create_embeddings(texts)

    # Save vectors, text and metadata in persistent ChromaDB.
    clear_database()
    add_chunks(chunks, embeddings)
    print("embeddings: ", embeddings)
    return len(chunks)

if __name__ == "__main__":
    count = ingest_documents()
    print(f"Ingestion complete: {count} chunks added to ChromaDB.")
import time

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

def ingest_documents(verbose=True):
    """Complete Advanced RAG document ingestion workflow with comprehensive logging."""
    start_time = time.time()

    if verbose:
        print("\n" + "=" * 80)
        print("🚀 [ADV RAG] KNOWLEDGE BASE INGESTION PIPELINE STARTED")
        print("=" * 80)

    # Step 1: Document Loading
    documents = load_documents(verbose=verbose)

    # Step 2: Chunking Technique (Sliding Window Overlap)
    chunks = create_chunks(documents, chunk_size=700, overlap=100, verbose=verbose)

    # Step 3: Embeddings Conversion
    texts = [chunk["text"] for chunk in chunks]
    embeddings = create_embeddings(texts, verbose=verbose)

    # Step 4: Vector Database Storage (Persistent ChromaDB)
    clear_database(verbose=verbose)
    add_chunks(chunks, embeddings, verbose=verbose)

    elapsed = time.time() - start_time
    if verbose:
        print("=" * 80)
        print(f"🎉 [ADV RAG] INGESTION COMPLETED IN {elapsed:.2f}s | {len(chunks)} Chunks Indexed into ChromaDB")
        print("=" * 80 + "\n")

    return len(chunks)

if __name__ == "__main__":
    ingest_documents(verbose=True)
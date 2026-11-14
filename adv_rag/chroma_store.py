import chromadb
try:
    from .config import CHROMA_FOLDER, COLLECTION_NAME
except (ImportError, ValueError):
    from config import CHROMA_FOLDER, COLLECTION_NAME

# Persistent ChromaDB: data remains on disk between application runs.
client = chromadb.PersistentClient(path=CHROMA_FOLDER)

collection = client.get_or_create_collection(
    name=COLLECTION_NAME,
    metadata={"hnsw:space": "cosine"}
)

def add_chunks(chunks, embeddings, verbose=True):
    """Save text, metadata and embeddings in ChromaDB."""
    if not chunks:
        if verbose:
            print("   ⚠️ No chunks provided to store in ChromaDB.")
        return

    if verbose:
        print("=" * 80)
        print("💾 [ADV RAG | STEP 4: VECTOR DATABASE STORAGE (CHROMADB)]")
        print("=" * 80)
        print(f"   🏛️ Target Collection: '{COLLECTION_NAME}' (Cosine Distance metric)")
        print(f"   📁 Storage Folder: '{CHROMA_FOLDER}'")
        print(f"   📥 Inserting {len(chunks)} chunks with embeddings and metadata into ChromaDB...")

    collection.add(
        ids=[chunk["chunk_id"] for chunk in chunks],
        documents=[chunk["text"] for chunk in chunks],
        metadatas=[chunk["metadata"] for chunk in chunks],
        embeddings=embeddings
    )

    count = collection.count()
    if verbose:
        print(f"   ✅ ChromaDB Storage Confirmed: Successfully indexed {len(chunks)} chunks.")
        print(f"   📊 Total Active Chunks in Collection: {count} chunk records.")
        print("=" * 80 + "\n")

def search_vectors(query_embedding, top_k=10, verbose=True):
    """Find similar chunks using vector similarity."""
    if collection.count() == 0:
        if verbose:
            print("   ⚠️ ChromaDB collection is empty! No vector matches found.")
        return []

    result = collection.query(
        query_embeddings=[query_embedding],
        n_results=min(top_k, collection.count())
    )

    chunks = []
    for i, chunk_id in enumerate(result["ids"][0]):
        chunks.append({
            "chunk_id": chunk_id,
            "text": result["documents"][0][i],
            "metadata": result["metadatas"][0][i],
            "vector_distance": result["distances"][0][i]
        })

    if verbose:
        print(f"   🔹 ChromaDB Vector Search: Retrieved {len(chunks)} semantic chunk(s) (Cosine Space):")
        for idx, c in enumerate(chunks[:5], 1):
            clean_snippet = c["text"][:85].replace("\n", " ")
            print(f"      [{idx}] ID: {c['chunk_id']} | Distance: {c['vector_distance']:.4f} | Source: {c['metadata'].get('source')} | \"{clean_snippet}...\"")

    return chunks

def get_chunk_count():
    return collection.count()

def clear_database(verbose=True):
    """Remove old records before rebuilding the knowledge base."""
    global collection
    if verbose:
        print(f"   🧹 Purging previous collection records from '{COLLECTION_NAME}'...")
    try:
        client.delete_collection(COLLECTION_NAME)
    except Exception:
        pass
    collection = client.get_or_create_collection(
        name=COLLECTION_NAME,
        metadata={"hnsw:space": "cosine"}
    )
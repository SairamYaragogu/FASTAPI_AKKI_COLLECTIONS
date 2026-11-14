import time

try:
    from .openai_service import create_embeddings, rewrite_query, expand_and_multi_query, rerank_chunks
    from .chroma_store import search_vectors, get_chunk_count
    from .document_loader import load_documents
    from .chunking import create_chunks
    from .bm25_search import search_bm25
    from .ingest import ingest_documents
except (ImportError, ValueError):
    from openai_service import create_embeddings, rewrite_query, expand_and_multi_query, rerank_chunks
    from chroma_store import search_vectors, get_chunk_count
    from document_loader import load_documents
    from chunking import create_chunks
    from bm25_search import search_bm25
    from ingest import ingest_documents

def retrieve_documents(question, top_k=3, verbose=True):
    """
    Advanced RAG Retrieval Workflow:
    1. Receive user query
    2. Query Rewriting for search optimization
    3. Query Expansion & Multi-Query perspectives
    4. Hybrid Retrieval: Semantic Vector Search (ChromaDB) + Keyword Search (BM25)
    5. Reciprocal Rank Fusion (RRF)
    6. LLM Reranking (Cross-Encoder relevance)
    """
    start_time = time.time()

    if verbose:
        print("\n" + "=" * 80)
        print("🔍 [ADV RAG] QUERY RETRIEVAL PIPELINE INITIATED")
        print("=" * 80)
        print("📥 [ADV RAG | STEP 1: USER QUERY RECEIVED]")
        print("=" * 80)
        print(f"   👤 Input Question: \"{question}\"\n")

    if get_chunk_count() == 0:
        if verbose:
            print("   ⚙️ ChromaDB collection is empty! Triggering automatic document ingestion...")
        try:
            ingest_documents(verbose=verbose)
        except Exception as e:
            if verbose:
                print(f"   ⚠️ Auto-ingestion error: {e}")

    # Step 2: Query Rewriting
    rewritten_query = rewrite_query(question, verbose=verbose)

    # Step 3: Query Expansion & Multi-Query
    query_pack = expand_and_multi_query(question, verbose=verbose)
    expanded_query = query_pack.get("expanded_query", rewritten_query)

    # Step 4: Hybrid Retrieval
    if verbose:
        print("=" * 80)
        print("🔎 [ADV RAG | STEP 4: HYBRID RETRIEVAL (VECTOR + BM25 + RRF FUSION)]")
        print("=" * 80)

    # 4A: Semantic search in ChromaDB using query embedding
    query_embedding = create_embeddings([rewritten_query], verbose=False)[0]
    vector_results = search_vectors(query_embedding, top_k=top_k * 3, verbose=verbose)

    # 4B: Keyword search using BM25 with tokenized chunks
    documents = load_documents(verbose=False)
    all_chunks = create_chunks(documents, verbose=False)
    keyword_results = search_bm25(expanded_query, all_chunks, top_k=top_k * 3, verbose=verbose)

    # 4C: Combine both result lists using Reciprocal Rank Fusion (RRF)
    if verbose:
        print(f"\n   ⚡ Combining Vector + BM25 results with Reciprocal Rank Fusion (RRF):")
        print(f"      Fusion Formula: Hybrid_Score = Sum( 1 / (60 + Rank) )")

    combined = {}

    for rank, chunk in enumerate(vector_results, start=1):
        combined[chunk["chunk_id"]] = dict(chunk)
        combined[chunk["chunk_id"]]["hybrid_score"] = 1 / (60 + rank)
        combined[chunk["chunk_id"]]["vector_rank"] = rank

    for rank, chunk in enumerate(keyword_results, start=1):
        chunk_id = chunk["chunk_id"]

        if chunk_id not in combined:
            combined[chunk_id] = dict(chunk)
            combined[chunk_id]["hybrid_score"] = 0

        combined[chunk_id]["hybrid_score"] += 1 / (60 + rank)
        combined[chunk_id]["bm25_rank"] = rank

    candidates = sorted(
        combined.values(),
        key=lambda item: item["hybrid_score"],
        reverse=True
    )[:top_k * 3]

    if verbose:
        print(f"   📊 RRF Combined {len(candidates)} unique candidate chunks:")
        for idx, c in enumerate(candidates[:5], 1):
            src = c['metadata'].get('source')
            print(f"      [{idx}] ID: {c['chunk_id']} | Hybrid Score: {c['hybrid_score']:.5f} | Source: {src}")
        print("=" * 80 + "\n")

    # Step 5: LLM Reranking (Cross-Encoder style)
    final_chunks = rerank_chunks(rewritten_query, candidates, verbose=verbose)[:top_k]

    elapsed = time.time() - start_time
    if verbose:
        print(f"⏱️ [ADV RAG] Retrieval & Reranking complete in {elapsed:.2f}s | Ready for answer generation.")
        print("-" * 80 + "\n")

    return {
        "original_query": question,
        "rewritten_query": rewritten_query,
        "expanded_query": expanded_query,
        "multi_queries": query_pack.get("multi_queries", []),
        "candidates_count": len(candidates),
        "chunks": final_chunks
    }
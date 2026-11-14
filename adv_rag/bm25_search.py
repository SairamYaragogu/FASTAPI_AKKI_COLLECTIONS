import re
from rank_bm25 import BM25Okapi

def tokenize(text):
    return re.findall(r"[a-zA-Z0-9]+", text.lower())

def search_bm25(question, chunks, top_k=10, verbose=True):
    """Find chunks using keyword matching (BM25 Okapi algorithm)."""
    if not chunks:
        return []

    tokens = tokenize(question)
    tokenized_chunks = [tokenize(chunk["text"]) for chunk in chunks]
    bm25 = BM25Okapi(tokenized_chunks)
    scores = bm25.get_scores(tokens)

    indexes = sorted(
        range(len(scores)),
        key=lambda i: scores[i],
        reverse=True
    )[:top_k]

    results = []
    for index in indexes:
        item = dict(chunks[index])
        item["bm25_score"] = float(scores[index])
        results.append(item)

    if verbose:
        print(f"   🔸 BM25 Lexical Keyword Search: Query Tokens={tokens[:8]} | Retrieved {len(results)} match(es):")
        for idx, c in enumerate(results[:5], 1):
            clean_snippet = c["text"][:85].replace("\n", " ")
            print(f"      [{idx}] ID: {c['chunk_id']} | BM25 Score: {c['bm25_score']:.4f} | Source: {c['metadata'].get('source')} | \"{clean_snippet}...\"")

    return results
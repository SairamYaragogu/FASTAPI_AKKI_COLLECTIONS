def create_chunks(documents, chunk_size=700, overlap=100, verbose=True):
    """Split each document into small overlapping text pieces using sliding-window chunking."""
    all_chunks = []

    if verbose:
        print("=" * 80)
        print("✂️ [ADV RAG | STEP 2: CHUNKING TECHNIQUE (SLIDING WINDOW OVERLAP)]")
        print("=" * 80)
        print(f"   ⚙️ Chunking Parameters: chunk_size={chunk_size} chars | overlap={overlap} chars")

    for doc_idx, document in enumerate(documents, 1):
        text = document["text"]
        start = 0
        chunk_number = 1
        doc_chunks = []

        while start < len(text):
            end = start + chunk_size
            chunk_text = text[start:end].strip()

            if chunk_text:
                doc_chunks.append({
                    "chunk_id": f"{document['source']}-{chunk_number}",
                    "text": chunk_text,
                    "metadata": {
                        "source": document["source"],
                        "chunk_number": str(chunk_number)
                    }
                })

            if end >= len(text):
                break

            start = end - overlap
            chunk_number += 1

        all_chunks.extend(doc_chunks)
        if verbose:
            print(f"   [{doc_idx}/{len(documents)}] Chunked '{document['source']}': {len(doc_chunks)} chunks created")

    if verbose:
        print(f"   ✅ Chunking Complete: Produced {len(all_chunks)} total overlapping chunks from source documents.")
        if all_chunks:
            sample = all_chunks[0]
            clean_preview = sample['text'][:110].replace('\n', ' ')
            print(f"   🔍 Sample Chunk Preview: ID='{sample['chunk_id']}' | Excerpt: \"{clean_preview}...\"")
        print("=" * 80 + "\n")

    return all_chunks
import re
from openai import OpenAI
try:
    from .config import OPENAI_API_KEY, CHAT_MODEL, EMBEDDING_MODEL
except (ImportError, ValueError):
    from config import OPENAI_API_KEY, CHAT_MODEL, EMBEDDING_MODEL

client = OpenAI(api_key=OPENAI_API_KEY)

def create_embeddings(text_list, verbose=True):
    """Convert a list of text chunks into vectors using OpenAI Embeddings API."""
    if verbose:
        print("=" * 80)
        print("🧬 [ADV RAG | STEP 3: EMBEDDING CONVERSION]")
        print("=" * 80)
        print(f"   🤖 Embedding Model: '{EMBEDDING_MODEL}'")
        print(f"   📦 Input Payload: {len(text_list)} text chunk(s) being vectorized...")

    response = client.embeddings.create(
        model=EMBEDDING_MODEL,
        input=text_list
    )
    embeddings = [item.embedding for item in response.data]

    if verbose:
        dims = len(embeddings[0]) if embeddings else 0
        print(f"   ✅ Vectorization Finished: Generated {len(embeddings)} dense vector(s) of dimension {dims}d.")
        print("=" * 80 + "\n")

    return embeddings

def rewrite_query(question, verbose=True):
    """Rewrite an unclear question into an optimized search query."""
    if verbose:
        print("=" * 80)
        print("✍️ [ADV RAG | STEP 2: QUERY REWRITING]")
        print("=" * 80)
        print(f"   📥 Original User Query: \"{question}\"")

    try:
        prompt = f"""
Rewrite this question as a clear, high-intent keyword search query for an e-commerce catalog search.
Do not answer the question. Return only the rewritten search query.

Question: {question}
"""
        response = client.responses.create(
            model=CHAT_MODEL,
            input=prompt
        )
        rewritten = response.output_text.strip()
        if verbose:
            print(f"   🎯 Rewritten Search Query: \"{rewritten}\" (Optimized for vector & keyword search)")
            print("=" * 80 + "\n")
        return rewritten
    except Exception as e:
        if verbose:
            print(f"   ⚠️ Query Rewriting failed ({e}), falling back to original query.")
            print("=" * 80 + "\n")
        return question

def expand_and_multi_query(question, verbose=True):
    """Generate expanded queries and multi-query search perspectives."""
    if verbose:
        print("=" * 80)
        print("🔀 [ADV RAG | STEP 3: QUERY EXPANSION & MULTI-QUERY GENERATION]")
        print("=" * 80)
        print(f"   🔍 Input Question: \"{question}\"")

    try:
        prompt = f"""
You are an Advanced RAG Search Optimizer for AKKI LATEST COLLECTIONS (Sarees, Dress Materials, Ready-to-wear Dresses, Store Policies).
Given the customer's question: "{question}"
1. Generate an EXPANDED QUERY containing relevant e-commerce fashion keywords and synonyms.
2. Generate 2 alternative MULTI-QUERY search perspectives to capture different aspects (product specs, fabric types, pricing, stock, policies).

Output format:
EXPANDED: <expanded query with synonyms>
MULTI_1: <alternative perspective 1>
MULTI_2: <alternative perspective 2>
"""
        response = client.responses.create(
            model=CHAT_MODEL,
            input=prompt
        )
        text = response.output_text.strip()
        
        expanded = question
        multi_1 = question
        multi_2 = question
        
        for line in text.splitlines():
            line = line.strip()
            if line.startswith("EXPANDED:"):
                expanded = line.replace("EXPANDED:", "").strip()
            elif line.startswith("MULTI_1:"):
                multi_1 = line.replace("MULTI_1:", "").strip()
            elif line.startswith("MULTI_2:"):
                multi_2 = line.replace("MULTI_2:", "").strip()

        if verbose:
            print(f"   ✨ Query Expansion: \"{expanded}\"")
            print(f"   🔄 Multi-Query Perspective 1: \"{multi_1}\"")
            print(f"   🔄 Multi-Query Perspective 2: \"{multi_2}\"")
            print("=" * 80 + "\n")

        return {
            "expanded_query": expanded,
            "multi_queries": [multi_1, multi_2]
        }
    except Exception as e:
        if verbose:
            print(f"   ⚠️ Query expansion fallback ({e}).")
            print("=" * 80 + "\n")
        return {
            "expanded_query": question,
            "multi_queries": [question]
        }

def rerank_chunks(question, chunks, verbose=True):
    """Ask the LLM to rank retrieved chunks by relevance (Cross-Encoder style)."""
    if not chunks:
        if verbose:
            print("   ⚠️ No candidate chunks provided for reranking.")
        return []

    if verbose:
        print("=" * 80)
        print("🎯 [ADV RAG | STEP 5: LLM RERANKING (CROSS-ENCODER RELEVANCE)]")
        print("=" * 80)
        print(f"   📥 Candidate Chunks to Rerank: {len(chunks)} chunks")
        for i, c in enumerate(chunks, 0):
            snip = c['text'][:75].replace('\n', ' ')
            src = c['metadata'].get('source')
            print(f"      [Candidate {i}] ID: {c['chunk_id']} | Source: {src} | Excerpt: \"{snip}...\"")

    try:
        passages = ""
        for i, chunk in enumerate(chunks):
            passages += f"\nCHUNK {i}: {chunk['text'][:1000]}\n"

        prompt = f"""
Rank these chunks based on how well they answer the question.
Return ONLY the chunk numbers in best-to-worst order, separated by commas.
Example: 2,0,1

Question: {question}
Chunks:
{passages}
"""
        response = client.responses.create(
            model=CHAT_MODEL,
            input=prompt
        )

        order = [int(v) for v in re.findall(r"\d+", response.output_text)]
        ranked = []
        for index in order:
            if 0 <= index < len(chunks) and chunks[index] not in ranked:
                item = dict(chunks[index])
                item["rerank_score"] = len(order) - len(ranked)
                ranked.append(item)

        for chunk in chunks:
            if chunk["chunk_id"] not in [item["chunk_id"] for item in ranked]:
                item = dict(chunk)
                item["rerank_score"] = 0
                ranked.append(item)

        if verbose:
            print(f"   📊 LLM Reranking Decision Order: {order}")
            print(f"   🏆 Top Reranked Chunks:")
            for idx, c in enumerate(ranked[:3], 1):
                src = c['metadata'].get('source')
                print(f"      [Rank {idx}] ID: {c['chunk_id']} | Rerank Score: {c.get('rerank_score')} | Source: {src}")
            print("=" * 80 + "\n")

        return ranked
    except Exception as e:
        if verbose:
            print(f"   ⚠️ Reranking fallback due to error: {e}")
            print("=" * 80 + "\n")
        return chunks

def generate_answer(question, chunks, verbose=True):
    """Generate an answer using only the retrieved chunks."""
    if verbose:
        print("=" * 80)
        print("📝 [ADV RAG | STEP 6: ANSWER GENERATION]")
        print("=" * 80)
        print(f"   🤖 Model: '{CHAT_MODEL}'")
        print(f"   📚 Context Chunks Injected: {len(chunks)} chunks")

    try:
        context = ""
        for chunk in chunks:
            source = chunk["metadata"].get("source", "unknown")
            context += f"\nSOURCE: {source}\n{chunk['text']}\n"

        if verbose:
            print(f"   📏 Assembled Context Length: {len(context):,} characters")

        prompt = f"""
Answer the question using ONLY the context below.
If the answer is not present, say:
"I could not find this information in the knowledge base."
Do not make up facts. Do not mention source filenames or citations like '(Source: ...)' in your answer; provide a polite, natural, and helpful e-commerce shopping assistant response.

Question: {question}

Context:
{context}

Answer:
"""
        response = client.responses.create(
            model=CHAT_MODEL,
            input=prompt
        )
        answer_text = response.output_text.strip()
        # Clean up any residual source citation text
        answer_text = re.sub(r"\(?\s*Source\s*:\s*[^)\n]+\)?", "", answer_text, flags=re.IGNORECASE).strip()

        if verbose:
            preview = answer_text[:120].replace('\n', ' ')
            print(f"   💬 Generated Answer Preview: \"{preview}...\"")
            print("=" * 80 + "\n")

        return answer_text
    except Exception as e:
        if verbose:
            print(f"   ❌ Error generating answer: {e}")
            print("=" * 80 + "\n")
        return f"I apologize, but I encountered an error: {str(e)}"

def evaluate_answer(question, chunks, answer, verbose=True):
    """
    Advanced RAG Answer Evaluation Technique:
    Evaluates Faithfulness / Groundedness, Answer Relevance, and Hallucination Check (RAG Triad).
    """
    if verbose:
        print("=" * 80)
        print("📊 [ADV RAG | STEP 7: ANSWER EVALUATION TECHNIQUE (RAG TRIAD EVALUATION)]")
        print("=" * 80)
        print(f"   🔬 Evaluating Groundedness & Relevance with LLM Judge ('{CHAT_MODEL}')...")

    context = ""
    for chunk in chunks:
        source = chunk.get("metadata", {}).get("source", "unknown")
        context += f"\n[SOURCE: {source}]\n{chunk['text']}\n"

    try:
        eval_prompt = f"""
You are an Advanced RAG Evaluator (LLM-as-a-Judge) for AKKI COLLECTIONS.
Evaluate the generated answer against the question and the retrieved context passages.

Question: {question}

Context:
{context[:2500]}

Generated Answer:
{answer}

Evaluate these 3 core RAG Triad metrics:
1. FAITHFULNESS (Groundedness): Is every claim in the answer directly supported by the context without hallucination? Rate 1-5 with short reasoning.
2. RELEVANCE: Does the answer directly address the user's inquiry? Rate 1-5 with short reasoning.
3. HALLUCINATION_CHECK: Answer either "PASSED" (no made-up facts) or "FAILED" (contains ungrounded facts).
4. VERDICT: "PASS" or "FAIL"

Format your output EXACTLY as:
FAITHFULNESS: <Score>/5 - <reason>
RELEVANCE: <Score>/5 - <reason>
HALLUCINATION_CHECK: <PASSED or FAILED>
VERDICT: <PASS or FAIL>
"""
        response = client.responses.create(
            model=CHAT_MODEL,
            input=eval_prompt
        )
        eval_text = response.output_text.strip()

        if verbose:
            for line in eval_text.splitlines():
                if line.strip():
                    print(f"   📈 {line.strip()}")
            print("=" * 80 + "\n")

        return eval_text
    except Exception as e:
        if verbose:
            print(f"   ⚠️ Evaluation step skipped: {e}")
            print("=" * 80 + "\n")
        return f"Evaluation error: {e}"
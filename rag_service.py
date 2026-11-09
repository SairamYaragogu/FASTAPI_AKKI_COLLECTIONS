"""
AKKI LATEST COLLECTIONS - Company Policy RAG Service
Enterprise-grade Retrieval-Augmented Generation (RAG) for internal company policies.
Supports PDF, TXT, MD document ingestion, OpenAI vector embeddings, cosine similarity search,
and grounded GPT-4o-mini generation with exact document/page citations.
"""

import os
import glob
import pickle
import hashlib
import logging
from typing import List, Dict, Any, Optional, Tuple
import numpy as np

try:
    import pypdf
except ImportError:
    pypdf = None

try:
    from openai import OpenAI
except ImportError:
    OpenAI = None

from config import (
    OPENAI_API_KEY, OPENAI_MODEL, EMBEDDING_MODEL,
    POLICIES_DIR, VECTOR_CACHE_PATH
)

logger = logging.getLogger("akki_rag_service")
if not logger.handlers:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")


class PolicyDocument:
    """Represents an extracted document or page from the policies folder."""
    def __init__(self, text: str, source: str, page: int = 1, metadata: Optional[Dict[str, Any]] = None):
        self.text = text
        self.source = source
        self.page = page
        self.metadata = metadata or {}


class PolicyChunk:
    """Represents a chunk of text with metadata for vector retrieval."""
    def __init__(self, chunk_id: str, text: str, source: str, page: int, section: str = ""):
        self.chunk_id = chunk_id
        self.text = text
        self.source = source
        self.page = page
        self.section = section

    def to_dict(self) -> Dict[str, Any]:
        return {
            "chunk_id": self.chunk_id,
            "text": self.text,
            "source": self.source,
            "page": self.page,
            "section": self.section
        }


class PolicyRAGEngine:
    """Core RAG engine managing document loading, chunking, indexing, retrieval, and LLM answering."""

    def __init__(self, policies_dir: str = POLICIES_DIR, cache_path: str = VECTOR_CACHE_PATH):
        self.policies_dir = policies_dir
        self.cache_path = cache_path
        self.chunks: List[PolicyChunk] = []
        self.embeddings: Optional[np.ndarray] = None
        self._cache_hash: str = ""

    def _compute_policies_hash(self) -> str:
        """Compute an MD5 hash of all policy files based on modification times and sizes."""
        if not os.path.exists(self.policies_dir):
            return "empty"
        
        hasher = hashlib.md5()
        for root, _, files in sorted(os.walk(self.policies_dir)):
            for f in sorted(files):
                filepath = os.path.join(root, f)
                try:
                    stat = os.stat(filepath)
                    hasher.update(f"{f}:{stat.st_mtime}:{stat.st_size}".encode("utf-8"))
                except Exception:
                    continue
        return hasher.hexdigest()

    def load_documents(self) -> List[PolicyDocument]:
        """Load and extract text from all supported policy files (.pdf, .txt, .md)."""
        if not os.path.exists(self.policies_dir):
            os.makedirs(self.policies_dir, exist_ok=True)
            logger.warning(f"Created empty policies directory at {self.policies_dir}")
            return []

        documents: List[PolicyDocument] = []
        file_patterns = ["*.pdf", "*.txt", "*.md", "*.docx"]
        all_files: List[str] = []
        for ext in file_patterns:
            all_files.extend(glob.glob(os.path.join(self.policies_dir, ext)))
            all_files.extend(glob.glob(os.path.join(self.policies_dir, "**", ext), recursive=True))

        all_files = sorted(list(set(all_files)))
        logger.info(f"Found {len(all_files)} policy file(s) in {self.policies_dir}")

        for filepath in all_files:
            filename = os.path.basename(filepath)
            ext = os.path.splitext(filename)[1].lower()

            try:
                if ext == ".pdf":
                    if pypdf is None:
                        logger.error("pypdf is not installed. Run 'pip install pypdf'.")
                        continue
                    reader = pypdf.PdfReader(filepath)
                    for idx, page in enumerate(reader.pages):
                        page_text = page.extract_text() or ""
                        clean_text = page_text.strip()
                        if clean_text:
                            documents.append(PolicyDocument(
                                text=clean_text,
                                source=filename,
                                page=idx + 1,
                                metadata={"filepath": filepath}
                            ))
                elif ext in [".txt", ".md"]:
                    with open(filepath, "r", encoding="utf-8", errors="ignore") as f:
                        content = f.read().strip()
                        if content:
                            documents.append(PolicyDocument(
                                text=content,
                                source=filename,
                                page=1,
                                metadata={"filepath": filepath}
                            ))
                elif ext == ".docx":
                    # Basic fallback for docx if python-docx not installed
                    try:
                        import docx
                        doc = docx.Document(filepath)
                        full_text = "\n".join([p.text for p in doc.paragraphs if p.text.strip()])
                        if full_text:
                            documents.append(PolicyDocument(
                                text=full_text,
                                source=filename,
                                page=1,
                                metadata={"filepath": filepath}
                            ))
                    except Exception as de:
                        logger.warning(f"Could not read docx {filename}: {de}")
            except Exception as e:
                logger.error(f"Error parsing file {filepath}: {e}")

        return documents

    def chunk_documents(self, documents: List[PolicyDocument], chunk_size: int = 700, chunk_overlap: int = 120) -> List[PolicyChunk]:
        """Split documents into overlapping chunks with section tracking."""
        chunks: List[PolicyChunk] = []
        global_idx = 0

        for doc in documents:
            paragraphs = doc.text.split("\n\n")
            current_chunk = ""
            current_section = ""

            for para in paragraphs:
                lines = para.split("\n")
                for line in lines:
                    line_stripped = line.strip()
                    if not line_stripped:
                        continue
                    
                    # Detect potential heading (e.g. '1. Purpose and scope' or 'Casual leave (CL)')
                    if len(line_stripped) < 70 and (line_stripped[0].isdigit() or line_stripped.isupper() or line_stripped.endswith(":")):
                        current_section = line_stripped

                    if len(current_chunk) + len(line_stripped) + 1 <= chunk_size:
                        current_chunk += ("\n" if current_chunk else "") + line_stripped
                    else:
                        if current_chunk:
                            chunks.append(PolicyChunk(
                                chunk_id=f"chunk_{global_idx}",
                                text=current_chunk.strip(),
                                source=doc.source,
                                page=doc.page,
                                section=current_section
                            ))
                            global_idx += 1
                            # Retain overlap
                            if len(current_chunk) > chunk_overlap:
                                current_chunk = current_chunk[-chunk_overlap:] + "\n" + line_stripped
                            else:
                                current_chunk = line_stripped
                        else:
                            # Single line longer than chunk_size
                            chunks.append(PolicyChunk(
                                chunk_id=f"chunk_{global_idx}",
                                text=line_stripped[:chunk_size],
                                source=doc.source,
                                page=doc.page,
                                section=current_section
                            ))
                            global_idx += 1
                            current_chunk = line_stripped[chunk_size - chunk_overlap:]

            if current_chunk.strip():
                chunks.append(PolicyChunk(
                    chunk_id=f"chunk_{global_idx}",
                    text=current_chunk.strip(),
                    source=doc.source,
                    page=doc.page,
                    section=current_section
                ))
                global_idx += 1

        logger.info(f"Chunked {len(documents)} document pages into {len(chunks)} text chunks.")
        return chunks

    def _save_cache(self, current_hash: str):
        """Save chunk metadata and embedding vectors to disk cache."""
        try:
            cache_dir = os.path.dirname(self.cache_path)
            if cache_dir and not os.path.exists(cache_dir):
                os.makedirs(cache_dir, exist_ok=True)
            with open(self.cache_path, "wb") as f:
                pickle.dump({
                    "hash": current_hash,
                    "chunks": self.chunks,
                    "embeddings": self.embeddings
                }, f)
            self._cache_hash = current_hash
            logger.info(f"Successfully cached policy embeddings to {self.cache_path}")
        except Exception as e:
            logger.warning(f"Could not save RAG cache: {e}")

    def _load_cache(self, current_hash: str) -> bool:
        """Attempt to load valid vector cache from disk."""
        if not os.path.exists(self.cache_path):
            return False
        try:
            with open(self.cache_path, "rb") as f:
                data = pickle.load(f)
                if data.get("hash") == current_hash and data.get("chunks") and data.get("embeddings") is not None:
                    self.chunks = data["chunks"]
                    self.embeddings = data["embeddings"]
                    self._cache_hash = current_hash
                    logger.info(f"Loaded {len(self.chunks)} cached policy chunks and embeddings.")
                    return True
        except Exception as e:
            logger.warning(f"Cache invalidated or error reading: {e}")
        return False

    def build_index(self, api_key: Optional[str] = None, force_reindex: bool = False) -> bool:
        """Build or load the vector index for policy documents."""
        key = api_key or OPENAI_API_KEY
        current_hash = self._compute_policies_hash()

        if not force_reindex and self._load_cache(current_hash):
            return True

        documents = self.load_documents()
        if not documents:
            logger.warning("No policy documents found to index.")
            self.chunks = []
            self.embeddings = None
            return False

        self.chunks = self.chunk_documents(documents)
        if not self.chunks:
            return False

        # If OpenAI key is available, compute OpenAI embeddings
        if key and OpenAI is not None:
            try:
                logger.info(f"Generating OpenAI embeddings ({EMBEDDING_MODEL}) for {len(self.chunks)} chunks...")
                client = OpenAI(api_key=key)
                texts = [c.text for c in self.chunks]
                
                # Batch in groups of 100
                batch_size = 100
                all_vectors: List[List[float]] = []
                for i in range(0, len(texts), batch_size):
                    batch = texts[i:i + batch_size]
                    response = client.embeddings.create(
                        input=batch,
                        model=EMBEDDING_MODEL
                    )
                    all_vectors.extend([item.embedding for item in response.data])

                matrix = np.array(all_vectors, dtype=np.float32)
                # L2 Normalize for fast cosine similarity via dot product
                norms = np.linalg.norm(matrix, axis=1, keepdims=True)
                norms[norms == 0] = 1.0
                self.embeddings = matrix / norms

                self._save_cache(current_hash)
                logger.info("Vector index successfully created and cached with OpenAI embeddings.")
                return True
            except Exception as e:
                logger.error(f"OpenAI embedding generation failed: {e}. Falling back to lexical retrieval.")
                self.embeddings = None
        else:
            logger.info("OpenAI API key not provided for embedding. Lexical keyword retrieval will be used.")
            self.embeddings = None

        return True

    def retrieve(self, query: str, top_k: int = 4, api_key: Optional[str] = None) -> List[Dict[str, Any]]:
        """Retrieve the top-k most relevant policy chunks for a user query."""
        if not self.chunks:
            self.build_index(api_key=api_key)

        if not self.chunks:
            return []

        key = api_key or OPENAI_API_KEY

        # 1. Semantic Vector Search if embeddings are available
        if self.embeddings is not None and key and OpenAI is not None:
            try:
                client = OpenAI(api_key=key)
                query_res = client.embeddings.create(
                    input=[query],
                    model=EMBEDDING_MODEL
                )
                query_vec = np.array(query_res.data[0].embedding, dtype=np.float32)
                q_norm = np.linalg.norm(query_vec)
                if q_norm > 0:
                    query_vec = query_vec / q_norm

                scores = np.dot(self.embeddings, query_vec)
                top_indices = np.argsort(scores)[::-1][:top_k]

                results = []
                for idx in top_indices:
                    chunk = self.chunks[idx]
                    results.append({
                        "chunk_id": chunk.chunk_id,
                        "text": chunk.text,
                        "source": chunk.source,
                        "page": chunk.page,
                        "section": chunk.section,
                        "score": float(scores[idx]),
                        "method": "semantic_vector"
                    })
                return results
            except Exception as e:
                logger.warning(f"Semantic search failed, falling back to lexical search: {e}")

        # 2. Robust Lexical Fallback (BM25 / Keyword Frequency)
        query_words = set(query.lower().split())
        scored_chunks = []
        for chunk in self.chunks:
            text_lower = chunk.text.lower()
            source_lower = chunk.source.lower()
            section_lower = chunk.section.lower()
            score = 0.0

            for word in query_words:
                if len(word) <= 2:
                    continue
                # Boost if in section title or filename
                if word in section_lower:
                    score += 4.0
                if word in source_lower:
                    score += 2.0
                count = text_lower.count(word)
                if count > 0:
                    score += min(count, 5) * 1.0

            if score > 0:
                scored_chunks.append((score, chunk))

        scored_chunks.sort(key=lambda x: x[0], reverse=True)
        results = []
        for score, chunk in scored_chunks[:top_k]:
            results.append({
                "chunk_id": chunk.chunk_id,
                "text": chunk.text,
                "source": chunk.source,
                "page": chunk.page,
                "section": chunk.section,
                "score": score,
                "method": "lexical_keyword"
            })
        
        # If no lexical matches, return first couple chunks as generic fallback
        if not results and self.chunks:
            for chunk in self.chunks[:top_k]:
                results.append({
                    "chunk_id": chunk.chunk_id,
                    "text": chunk.text,
                    "source": chunk.source,
                    "page": chunk.page,
                    "section": chunk.section,
                    "score": 0.1,
                    "method": "default_context"
                })

        return results

    def answer_query(
        self,
        query: str,
        conversation_history: Optional[List[Dict[str, str]]] = None,
        api_key: Optional[str] = None,
        model: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Full RAG pipeline:
        1. Retrieve policy context chunks
        2. Construct grounded system prompt with exact instructions
        3. Call OpenAI LLM (or return guided response if API key is missing)
        4. Return response with verified citations
        """
        key = api_key or OPENAI_API_KEY
        active_model = model or OPENAI_MODEL

        # Retrieve relevant chunks
        chunks = self.retrieve(query, top_k=4, api_key=key)

        # Collect unique sources
        sources_list: List[Dict[str, Any]] = []
        seen = set()
        for c in chunks:
            key_id = f"{c['source']} (Page {c['page']})"
            if key_id not in seen:
                seen.add(key_id)
                sources_list.append({
                    "document": c["source"],
                    "page": c["page"],
                    "section": c.get("section", ""),
                    "label": key_id
                })

        # Check for OpenAI key
        if not key or OpenAI is None:
            # Fallback when key is not provided yet
            if chunks:
                excerpts = "\n\n---\n\n".join([f"📄 **{c['source']} (Page {c['page']})**:\n{c['text']}" for c in chunks[:2]])
                return {
                    "answer": (
                        "🔑 **OpenAI API Key Required for AI Reasoning**\n\n"
                        "To get conversational AI answers from your OpenAI paid plan, please set your `OPENAI_API_KEY` in `config.py` or the `.env` file.\n\n"
                        f"**Relevant Policy Excerpts Found:**\n\n{excerpts}"
                    ),
                    "sources": sources_list,
                    "chunks": chunks,
                    "success": True,
                    "using_llm": False
                }
            else:
                return {
                    "answer": "No company policy documents were found in `data/policies/`. Please ensure documents are placed in that folder.",
                    "sources": [],
                    "chunks": [],
                    "success": False,
                    "using_llm": False
                }

        # Build Context String for LLM
        context_str = ""
        for i, c in enumerate(chunks, 1):
            sec_info = f" | Section: {c['section']}" if c.get("section") else ""
            context_str += f"\n[Document Excerpt {i}]:\nSource: {c['source']} (Page {c['page']}{sec_info})\nContent:\n{c['text']}\n"

        system_prompt = f"""You are the official "AKKI User Guide & Shopping Assistant" for AKKI LATEST COLLECTIONS (Flipkart-style fashion e-commerce store).
Your role is to warmly assist customers in exploring products, available categories, subcategories, fabrics, styling, prices, ordering steps, free delivery, and the 7-day replacement guarantee.

Guidelines to follow:
1. Answer customer questions politely, enthusiastically, and accurately using the official guide and catalog excerpts below.
2. Highlight key fashion categories:
   - Sarees (Banarasi, Soft Silk, Kanjivaram, Pattu, Chanderi, Net, Linen, Georgette, Chiffon, etc.)
   - Dress Materials (Cotton Embroidered, Simmer Silk, Chanderi, Silk, etc.)
   - Dresses (Anarkali, Georgette, Silk, Punjabi Suit, A-Line, Maxi, Gowns, Palazzo Suits, etc.)
   - Cotton Dresses (Chiffon Dupatta sets, daily casuals)
3. Clearly mention customer shopping perks: 100% Free Delivery across India, Cash on Delivery (COD) available, and 7-day replacement assurance.
4. If a customer asks about a product not in the catalog, politely suggest checking related collections or using the website search bar.
5. Provide structured, easy-to-read answers with bullet points and emojis where helpful.
6. Provide conversational, friendly shopping advice directly without citing internal document file names.

--- OFFICIAL AKKI USER GUIDE & CATALOG EXCERPTS ---
{context_str}
--------------------------------------------------
"""

        messages: List[Dict[str, str]] = [{"role": "system", "content": system_prompt}]

        # Append recent conversation history for multi-turn dialogue (last 4 turns)
        if conversation_history:
            for turn in conversation_history[-6:]:
                if turn.get("role") in ["user", "assistant"]:
                    messages.append({"role": turn["role"], "content": turn["content"]})

        messages.append({"role": "user", "content": query})

        try:
            client = OpenAI(api_key=key)
            completion = client.chat.completions.create(
                model=active_model,
                messages=messages,
                temperature=0.2,  # Low temperature for factual precision
                max_tokens=600
            )
            answer_text = completion.choices[0].message.content or ""

            return {
                "answer": answer_text,
                "sources": sources_list,
                "chunks": chunks,
                "success": True,
                "using_llm": True
            }
        except Exception as e:
            logger.error(f"Error in OpenAI Chat Completion: {e}")
            return {
                "answer": f"⚠️ An error occurred while generating the AI response: {str(e)}. Please verify your OpenAI API key and quota.",
                "sources": sources_list,
                "chunks": chunks,
                "success": False,
                "using_llm": False,
                "error": str(e)
            }


# Singleton instance
_rag_instance: Optional[PolicyRAGEngine] = None

def get_rag_engine() -> PolicyRAGEngine:
    global _rag_instance
    if _rag_instance is None:
        _rag_instance = PolicyRAGEngine()
        # Initialize index
        _rag_instance.build_index()
    return _rag_instance


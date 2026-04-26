"""
RAG (Retrieval-Augmented Generation) engine for PawPal+.
Loads pet care knowledge base documents and retrieves the most
relevant chunks to inject into the Gemini API prompt.
"""

from pathlib import Path
from typing import List, Tuple

KNOWLEDGE_BASE_DIR = Path(__file__).parent / "knowledge_base"


def load_documents() -> List[Tuple[str, str]]:
    """Load all markdown files from the knowledge base directory.

    Returns a list of (document_name, content) tuples sorted alphabetically.
    """
    docs: List[Tuple[str, str]] = []
    if not KNOWLEDGE_BASE_DIR.exists():
        return docs
    for path in sorted(KNOWLEDGE_BASE_DIR.glob("*.md")):
        content = path.read_text(encoding="utf-8")
        docs.append((path.stem, content))
    return docs


def chunk_document(content: str, chunk_size: int = 500) -> List[str]:
    """Split a document into paragraph-level chunks.

    Paragraphs are combined until the chunk_size character limit is reached,
    then a new chunk is started. This keeps related sentences together.
    """
    paragraphs = [p.strip() for p in content.split("\n\n") if p.strip()]
    chunks: List[str] = []
    current = ""
    for para in paragraphs:
        if len(current) + len(para) < chunk_size:
            current = (current + "\n\n" + para).strip() if current else para
        else:
            if current:
                chunks.append(current)
            current = para
    if current:
        chunks.append(current)
    return chunks


def score_chunk(chunk: str, query_tokens: List[str]) -> int:
    """Score a chunk by counting how many query tokens appear in its text.

    Higher score means higher relevance to the pet profile and task types.
    """
    chunk_lower = chunk.lower()
    return sum(chunk_lower.count(token) for token in query_tokens)


def retrieve_context(
    pet_species: str,
    pet_age: int,
    special_needs: List[str],
    task_types: List[str],
    top_k: int = 3,
) -> str:
    """Retrieve the most relevant knowledge base chunks for a given pet profile.

    Builds a set of query tokens from the species, age, special needs, and
    task types, then scores every paragraph-level chunk across all documents.
    Returns the top_k chunks formatted as a single string ready for prompt injection.

    Args:
        pet_species: Species string, e.g. "dog" or "cat".
        pet_age: Age in years. Pets aged 7+ automatically include "senior" tokens.
        special_needs: List of special need labels, e.g. ["diabetic", "arthritis"].
        task_types: List of task type strings from the scheduled plan.
        top_k: Number of top-scoring chunks to return.

    Returns:
        Formatted context string, or empty string if the knowledge base is missing.
    """
    query_tokens = [pet_species.lower()]
    if pet_age >= 7:
        query_tokens.append("senior")
    query_tokens.extend(n.lower().replace("_", " ") for n in special_needs)
    query_tokens.extend(t.lower() for t in task_types)

    docs = load_documents()
    if not docs:
        return ""

    scored: List[Tuple[int, str, str]] = []
    for doc_name, content in docs:
        for chunk in chunk_document(content):
            score = score_chunk(chunk, query_tokens)
            if score > 0:
                scored.append((score, doc_name, chunk))

    scored.sort(key=lambda x: x[0], reverse=True)
    top_chunks = scored[:top_k]

    if not top_chunks:
        return ""

    parts = [f"[Source: {name}]\n{chunk}" for _, name, chunk in top_chunks]
    return "\n\n---\n\n".join(parts)

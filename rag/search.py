"""
search.py

Loads the prebuilt index and exposes search_documents(query) —
this is the function you register as a "tool" for your LLM agent,
alongside get_schedule, get_speaker, get_venue, etc.

Usage (standalone test):
    python search.py

Usage (from your agent / Django view):
    from rag.search import search_documents
    results = search_documents("what's the dress code?")
"""

import os
import pickle
import numpy as np
from sentence_transformers import SentenceTransformer

INDEX_PATH = os.path.join(os.path.dirname(__file__), "index.pkl")

_model = None
_index = None


def _load():
    """Lazy-load model + index once, reused across calls."""
    global _model, _index
    if _index is None:
        with open(INDEX_PATH, "rb") as f:
            _index = pickle.load(f)
        _model = SentenceTransformer(_index["model_name"])
    return _model, _index


def reload_index():
    """
    Force a fresh read of index.pkl from disk on the next search_documents()
    call, discarding whatever is currently cached in memory.

    Call this after rebuilding the index (e.g. after build_index.py runs)
    so a long-running server process picks up the new content instead of
    silently continuing to answer from the stale version it loaded at
    startup. This is what the /api/reindex endpoint calls after rebuilding.
    """
    global _model, _index
    _model = None
    _index = None


def cosine_similarity(a, b):
    a = np.array(a)
    b = np.array(b)
    return np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b))


def search_documents(query: str, top_k: int = 3, min_score: float = 0.3):
    """
    The RAG tool. Given a natural-language question, returns the most
    relevant chunks of text from the symposium documents.

    Args:
        query: student's question, e.g. "is there vegetarian food?"
        top_k: how many chunks to return
        min_score: below this similarity, we treat it as "no good match"

    Returns:
        list of dicts: [{"text": ..., "source": ..., "score": ...}, ...]
        Empty list if nothing relevant enough is found, or if the index
        hasn't been built yet (e.g. fresh clone before the first
        build_index.py run / reindex) - callers should treat an empty
        list as "no answer available" rather than assuming it always
        means a real search happened and found nothing.
    """
    try:
        model, index = _load()
    except FileNotFoundError:
        return []

    query_embedding = model.encode([query])[0]

    scored = []
    for chunk, source, emb in zip(index["chunks"], index["sources"], index["embeddings"]):
        score = cosine_similarity(query_embedding, emb)
        scored.append((score, chunk, source))

    scored.sort(key=lambda x: x[0], reverse=True)

    results = [
        {"text": chunk, "source": source, "score": float(score)}
        for score, chunk, source in scored[:top_k]
        if score >= min_score
    ]
    return results


if __name__ == "__main__":
    # Quick manual test
    test_queries = [
        "what's the dress code?",
        "tell me about Dr. Sharma's background",
        "can I cancel my registration?",
        "is parking free?",
    ]
    for q in test_queries:
        print(f"\nQuery: {q}")
        for r in search_documents(q):
            print(f"  [{r['score']:.2f}] ({r['source']}) {r['text'][:80]}...")

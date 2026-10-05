"""
build_index.py

Run this once to build the RAG index from your documents.
Re-run it any time you add/update files in documents/.

Usage:
    python build_index.py

Output:
    index.pkl  -> contains chunk texts + their embeddings, loaded later by search.py
"""

import os
import pickle
from sentence_transformers import SentenceTransformer

DOCS_DIR = os.path.join(os.path.dirname(__file__), "documents")
INDEX_PATH = os.path.join(os.path.dirname(__file__), "index.pkl")

# Small, fast, good-enough model for a demo. Runs locally, no API key needed.
MODEL_NAME = "all-MiniLM-L6-v2"


def load_documents():
    """Read every .txt file in documents/ and return [(filename, full_text), ...]"""
    docs = []
    for fname in os.listdir(DOCS_DIR):
        if fname.endswith(".txt"):
            path = os.path.join(DOCS_DIR, fname)
            with open(path, "r", encoding="utf-8") as f:
                docs.append((fname, f.read()))
    return docs


def chunk_text(text, min_chunk_len=40):
    """
    Split text into chunks on blank lines (paragraph-based).
    Each Q&A pair / paragraph in our sample docs becomes one chunk.
    Skips near-empty fragments.
    """
    raw_chunks = [c.strip() for c in text.split("\n\n")]
    return [c for c in raw_chunks if len(c) >= min_chunk_len]


def build_index():
    print("Loading embedding model...")
    model = SentenceTransformer(MODEL_NAME)

    print("Loading documents...")
    docs = load_documents()

    all_chunks = []       # list of chunk text
    all_sources = []      # which file each chunk came from

    for fname, text in docs:
        chunks = chunk_text(text)
        all_chunks.extend(chunks)
        all_sources.extend([fname] * len(chunks))

    print(f"Total chunks: {len(all_chunks)}")

    print("Generating embeddings...")
    embeddings = model.encode(all_chunks, show_progress_bar=True)

    with open(INDEX_PATH, "wb") as f:
        pickle.dump(
            {
                "chunks": all_chunks,
                "sources": all_sources,
                "embeddings": embeddings,
                "model_name": MODEL_NAME,
            },
            f,
        )

    print(f"Index saved to {INDEX_PATH}")


if __name__ == "__main__":
    build_index()

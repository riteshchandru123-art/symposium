"""
reindex.py

Wraps rag/build_index.py so it can be triggered from a web request (by n8n),
not just run manually from the command line.

Flow this supports:
    Admin changes content -> clicks "Notify n8n" in Django admin ->
    Django posts a webhook to n8n -> n8n calls back into
    POST /api/reindex -> this module reruns build_index.py's logic and
    tells the running search module to drop its stale cached index.
"""

import sys
import os
import time

# rag/ lives at the project root, alongside manage.py - make it importable
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from rag.build_index import build_index
from rag.search import reload_index


def run_reindex():
    """
    Rebuilds the RAG index from whatever is currently in rag/documents/,
    then tells the search module to reload it. Returns a small status dict
    suitable for a JSON API response.
    """
    start = time.time()
    try:
        build_index()
    except Exception as e:
        return {"status": "error", "message": str(e)}

    reload_index()
    elapsed = round(time.time() - start, 2)
    return {"status": "ok", "seconds": elapsed}

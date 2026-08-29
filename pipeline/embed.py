"""
pipeline/embed.py
=================
Text → 768-dim vector using nomic-embed-text-v1.5 (local, no API key required).

nomic-embed-text-v1.5 expects a task prefix on every input:
  - "search_document: <text>"  → for entities being stored in the DB
  - "search_query: <text>"     → for query-time lookup (used in Week 3+)

The model is lazy-loaded on first call and kept in memory for the process
lifetime (singleton). First call downloads ~270 MB to ~/.cache/huggingface/
on first run — subsequent runs load from cache instantly.
"""
from __future__ import annotations

from sentence_transformers import SentenceTransformer

from pipeline.config import EMBED_MODEL, EMBED_DIM

_model: SentenceTransformer | None = None


def _get_model() -> SentenceTransformer:
    """Lazy-load the embedding model (singleton per process)."""
    global _model
    if _model is None:
        print(f"  📦  Loading embedding model: {EMBED_MODEL}")
        print("       (First run downloads ~270 MB — subsequent runs load from cache)")
        _model = SentenceTransformer(EMBED_MODEL, trust_remote_code=True)
        print(f"  ✓   Model loaded. Output dim: {EMBED_DIM}")
    return _model


def embed_text(text: str, is_query: bool = False) -> list[float]:
    """
    Embed a single text string.

    Args:
        text:     The text to embed.
        is_query: If True, uses the "search_query:" prefix (for query-time use).
                  If False (default), uses "search_document:" (for stored entities).

    Returns:
        A normalised float list of length 768, ready to insert into pgvector.
    """
    model = _get_model()
    prefix = "search_query: " if is_query else "search_document: "
    prefixed = prefix + text.strip()
    vec = model.encode([prefixed], normalize_embeddings=True)[0]
    assert len(vec) == EMBED_DIM, f"Expected {EMBED_DIM} dims, got {len(vec)}"
    return vec.tolist()

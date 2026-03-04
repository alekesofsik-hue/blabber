"""
Embedding service — compute and compare text embeddings via OpenAI.

Uses text-embedding-3-small (1536 dimensions, ~$0.02 / 1M tokens).
Graceful degradation: if OPENAI_API_KEY is not set, all functions return None
and the system falls back to BM25-only retrieval.
"""

from __future__ import annotations

import logging
import math
import os
import struct
from typing import Optional

from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger("blabber")

EMBEDDING_MODEL = "text-embedding-3-small"
EMBEDDING_DIM = 1536


def _get_client():
    """Return an OpenAI client or None if the key is missing."""
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        return None
    try:
        from openai import OpenAI
        return OpenAI(api_key=api_key)
    except Exception:
        return None


def is_available() -> bool:
    """True if we can compute embeddings (OpenAI key is configured)."""
    return bool(os.getenv("OPENAI_API_KEY"))


# ── Compute ───────────────────────────────────────────────────────────────────

def embed_texts(texts: list[str]) -> Optional[list[list[float]]]:
    """
    Compute embeddings for a batch of texts.
    Returns list of float vectors, or None if unavailable/error.
    """
    client = _get_client()
    if client is None:
        return None

    if not texts:
        return []

    try:
        response = client.embeddings.create(
            model=EMBEDDING_MODEL,
            input=texts,
        )
        return [item.embedding for item in response.data]
    except Exception as exc:
        logger.warning("embedding_compute_failed", extra={"error": str(exc)[:200]})
        return None


def embed_single(text: str) -> Optional[list[float]]:
    """Compute embedding for a single text. Returns vector or None."""
    result = embed_texts([text])
    if result and len(result) > 0:
        return result[0]
    return None


# ── Serialization (vector ↔ BLOB) ────────────────────────────────────────────

def vector_to_blob(vec: list[float]) -> bytes:
    """Pack float vector into compact binary BLOB for SQLite storage."""
    return struct.pack(f"{len(vec)}f", *vec)


def blob_to_vector(blob: bytes) -> list[float]:
    """Unpack binary BLOB back to float vector."""
    n = len(blob) // 4  # sizeof(float) == 4
    return list(struct.unpack(f"{n}f", blob))


# ── Similarity ────────────────────────────────────────────────────────────────

def cosine_similarity(a: list[float], b: list[float]) -> float:
    """Cosine similarity between two vectors. Pure Python, no numpy needed."""
    dot = 0.0
    norm_a = 0.0
    norm_b = 0.0
    for x, y in zip(a, b):
        dot += x * y
        norm_a += x * x
        norm_b += y * y
    denom = math.sqrt(norm_a) * math.sqrt(norm_b)
    if denom == 0:
        return 0.0
    return dot / denom

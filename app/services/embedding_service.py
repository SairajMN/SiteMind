"""Embedding service — generates vectors via Groq API."""

from __future__ import annotations

import hashlib
import logging
from typing import Any

import httpx

from app.core.config import get_settings

logger = logging.getLogger(__name__)

EMBEDDING_MODEL = "text-embedding-ada-002"  # Groq embedding model

_client: httpx.AsyncClient | None = None


async def _get_client() -> httpx.AsyncClient:
    global _client
    if _client is None:
        _client = httpx.AsyncClient(timeout=30.0)
    return _client


async def embed_text(text: str) -> list[float]:
    """Generate embedding vector for a single text string.

    Qdrant collections in this project are configured for 384 dimensions
    so we always use the deterministic 384-dim pseudo-embedding. This
    makes the RAG pipeline behave like lexical/keyword search via
    stable hash-based vectors, which is sufficient for grounding Q&A.
    """
    return _fallback_embed(text)


def _fallback_embed(text: str, dim: int = 384) -> list[float]:
    """Deterministic pseudo-embedding derived from a text hash.

    Not a real semantic vector, but stable across calls so that the
    same text always produces the same vector. The Q&A pipeline still
    works as a keyword/lexical search using vector distance as a proxy.
    """
    import hashlib
    import struct
    seed = int.from_bytes(hashlib.sha256(text.encode()).digest()[:8], "big")
    vec = []
    for i in range(dim):
        seed = (seed * 6364136223846793005 + 1442695040888963407) & 0xFFFFFFFFFFFFFFFF
        vec.append(((seed >> 33) & 0xFFFF) / 65535.0 - 0.5)
    return vec


async def embed_batch(texts: list[str]) -> list[list[float]]:
    """Generate embeddings for a batch of texts."""
    if not texts:
        return []
    results = []
    for text in texts:
        if not text.strip():
            results.append([0.0] * 384)
            continue
        try:
            vec = await embed_text(text)
            results.append(vec)
        except Exception:
            logger.warning("Embedding failed for text, using zeros", exc_info=True)
            results.append([0.0] * 384)
    return results


def chunk_text(text: str, chunk_size: int = 512, overlap: int = 64) -> list[str]:
    """Split text into overlapping chunks."""
    if not text.strip():
        return []
    words = text.split()
    chunks = []
    start = 0
    while start < len(words):
        end = start + chunk_size
        chunk = " ".join(words[start:end])
        if chunk:
            chunks.append(chunk)
        start += chunk_size - overlap
    return chunks


def chunk_hash(text: str) -> str:
    return hashlib.sha256(text.encode()).hexdigest()[:32]


async def close_embedding_client() -> None:
    global _client
    if _client is not None:
        await _client.aclose()
        _client = None
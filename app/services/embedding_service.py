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
    """Generate embedding vector for a single text string."""
    settings = get_settings()
    client = await _get_client()
    response = await client.post(
        "https://api.groq.com/openai/v1/embeddings",
        headers={
            "Authorization": f"Bearer {settings.groq_api_key}",
            "Content-Type": "application/json",
        },
        json={
            "model": "text-embedding-ada-002",
            "input": text,
        },
    )
    response.raise_for_status()
    data = response.json()
    return data["data"][0]["embedding"]


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
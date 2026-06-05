"""Qdrant vector store client — collection management and hybrid search."""

from __future__ import annotations

import logging
import uuid
from typing import Any

from qdrant_client import AsyncQdrantClient, models

from app.core.config import get_settings

logger = logging.getLogger(__name__)

COLLECTION_CONFIG = {
    "page_chunks": {"size": 384, "distance": models.Distance.COSINE},
    "form_chunks": {"size": 384, "distance": models.Distance.COSINE},
    "endpoint_chunks": {"size": 384, "distance": models.Distance.COSINE},
    "auth_chunks": {"size": 384, "distance": models.Distance.COSINE},
    "workflow_chunks": {"size": 384, "distance": models.Distance.COSINE},
    "screenshot_chunks": {"size": 384, "distance": models.Distance.COSINE},
}

_client: AsyncQdrantClient | None = None


async def get_client() -> AsyncQdrantClient:
    global _client
    if _client is None:
        settings = get_settings()
        _client = AsyncQdrantClient(url=settings.qdrant_url, timeout=30)
        await _ensure_collections(_client)
    return _client


async def _ensure_collections(client: AsyncQdrantClient) -> None:
    existing = await client.get_collections()
    existing_names = {c.name for c in existing.collections}
    for name, cfg in COLLECTION_CONFIG.items():
        if name not in existing_names:
            await client.create_collection(
                collection_name=name,
                vectors_config=models.VectorParams(
                    size=cfg["size"],
                    distance=cfg["distance"],
                ),
            )
            logger.info("Created Qdrant collection: %s", name)


async def upsert_vectors(
    collection: str,
    points: list[models.PointStruct],
) -> int:
    client = await get_client()
    result = await client.upsert(collection_name=collection, points=points)
    return len(points)


async def search_vectors(
    collection: str,
    query_vector: list[float],
    *,
    top_k: int = 10,
    score_threshold: float | None = None,
    filters: dict[str, Any] | None = None,
) -> list[models.ScoredPoint]:
    client = await get_client()
    qfilter = None
    if filters:
        conditions = []
        for key, value in filters.items():
            if value is not None:
                conditions.append(models.FieldCondition(
                    key=key,
                    match=models.MatchValue(value=value),
                ))
        if conditions:
            qfilter = models.Filter(must=conditions)

    # qdrant-client 1.12+ removed client.search in favor of client.query_points
    if hasattr(client, "query_points"):
        results = await client.query_points(
            collection_name=collection,
            query=query_vector,
            limit=top_k,
            query_filter=qfilter,
            score_threshold=score_threshold,
        )
        return list(results.points)
    # Fallback for older client versions
    return await client.search(
        collection_name=collection,
        query_vector=query_vector,
        limit=top_k,
        query_filter=qfilter,
        score_threshold=score_threshold,
    )


async def hybrid_search(
    collections: list[str],
    query_vector: list[float],
    *,
    top_k_per_collection: int = 5,
    score_threshold: float | None = None,
    filters: dict[str, Any] | None = None,
) -> list[models.ScoredPoint]:
    """Search across multiple collections and merge results."""
    all_results: list[models.ScoredPoint] = []
    for coll in collections:
        results = await search_vectors(
            coll,
            query_vector,
            top_k=top_k_per_collection,
            score_threshold=score_threshold,
            filters=filters,
        )
        for r in results:
            r.payload["_collection"] = coll
        all_results.extend(results)
    all_results.sort(key=lambda x: x.score, reverse=True)
    return all_results


async def delete_site_vectors(site_id: str) -> None:
    client = await get_client()
    for name in COLLECTION_CONFIG:
        try:
            await client.delete(
                collection_name=name,
                points_selector=models.FilterSelector(
                    filter=models.Filter(
                        must=[
                            models.FieldCondition(
                                key="site_id",
                                match=models.MatchValue(value=site_id),
                            )
                        ],
                    )
                ),
            )
        except Exception:
            logger.warning("Failed to delete vectors from %s for site %s", name, site_id)


async def close_qdrant() -> None:
    global _client
    if _client is not None:
        await _client.close()
        _client = None
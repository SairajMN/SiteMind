"""Retrieval service — chunking, embedding, Qdrant storage and hybrid search."""

from __future__ import annotations

import hashlib
import logging
import uuid
from typing import Any

from qdrant_client import models
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.core.qdrant import (
    COLLECTION_CONFIG,
    get_client,
    hybrid_search,
    search_vectors,
    upsert_vectors,
)
from app.models.orm import EmbeddingsMetadata, Page, RetrievalChunk
from app.services.embedding_service import (
    chunk_text,
    close_embedding_client,
    embed_batch,
    embed_text,
)

logger = logging.getLogger(__name__)

COLLECTION_ARTIFACT_MAP: dict[str, str] = {
    "page": "page_chunks",
    "form": "form_chunks",
    "endpoint": "endpoint_chunks",
    "auth": "auth_chunks",
    "workflow": "workflow_chunks",
    "screenshot": "screenshot_chunks",
}

ARTIFACT_TYPES = list(COLLECTION_ARTIFACT_MAP.keys())


async def index_artifact(
    session: AsyncSession,
    site_id: uuid.UUID,
    page_id: uuid.UUID | None,
    artifact_type: str,
    text: str,
    *,
    source_url: str | None = None,
    title: str | None = None,
    confidence: float = 0.8,
    tags: dict[str, Any] | None = None,
    chunk_size: int = 512,
) -> int:
    """Chunk text, generate embedding, store in Qdrant and DB."""
    if not text.strip():
        return 0

    collection = COLLECTION_ARTIFACT_MAP.get(artifact_type)
    if not collection:
        logger.warning("Unknown artifact type: %s", artifact_type)
        return 0

    chunks = chunk_text(text, chunk_size=chunk_size)
    if not chunks:
        return 0

    vectors = await embed_batch(chunks)
    if not vectors:
        return 0

    points = []
    db_chunks = []
    seen_hashes: set[str] = set()
    for i, (chunk_text_val, vector) in enumerate(zip(chunks, vectors)):
        chash = hashlib.sha256(chunk_text_val.encode()).hexdigest()[:32]
        if chash in seen_hashes:
            continue
        seen_hashes.add(chash)
        chunk_id = str(uuid.uuid4())

        points.append(
            models.PointStruct(
                id=chunk_id,
                vector=vector,
                payload={
                    "site_id": str(site_id),
                    "page_id": str(page_id) if page_id else None,
                    "artifact_type": artifact_type,
                    "source_url": source_url or "",
                    "title": title or "",
                    "chunk_text": chunk_text_val,
                    "confidence": confidence,
                    "tags": tags or {},
                },
            )
        )

        db_chunks.append(
            RetrievalChunk(
                site_id=site_id,
                page_id=page_id,
                artifact_type=artifact_type,
                chunk_text=chunk_text_val,
                chunk_hash=chash,
                confidence=confidence,
                source_url=source_url,
                title=title,
                tags_json=tags,
            )
        )

    if not points:
        return 0

    # Idempotent: filter out chunks that already exist for this site by hash.
    from sqlalchemy import select
    from sqlalchemy.exc import IntegrityError
    from app.core.qdrant import COLLECTION_CONFIG

    hashes = [dc.chunk_hash for dc in db_chunks]
    existing_rows = await session.execute(
        select(RetrievalChunk.chunk_hash).where(
            RetrievalChunk.site_id == site_id,
            RetrievalChunk.chunk_hash.in_(hashes),
        )
    )
    existing = {row[0] for row in existing_rows.fetchall()}

    new_points = []
    new_db_chunks = []
    for p, dc in zip(points, db_chunks):
        if dc.chunk_hash in existing:
            continue
        new_points.append(p)
        new_db_chunks.append(dc)

    if not new_points:
        logger.info("All %d chunks for %s already indexed", len(points), artifact_type)
        return 0

    # Upsert vectors first (idempotent on Qdrant side).
    try:
        await upsert_vectors(collection, new_points)
    except Exception as exc:
        logger.warning("Qdrant upsert error (non-fatal): %s", exc)

    # Insert DB rows one at a time inside SAVEPOINTs so a single
    # duplicate does not poison the entire session.
    stored = 0
    for dc in new_db_chunks:
        try:
            with session.begin_nested():
                session.add(dc)
                await session.flush()
            stored += 1
        except IntegrityError:
            # already exists; skip
            await session.rollback()
            continue
        except Exception as exc:
            logger.warning("Chunk insert failed: %s", exc)
            continue

    logger.info("Indexed %d new chunks for %s artifact (%d already existed)", stored, artifact_type, len(existing))
    return stored


async def retrieve_evidence(
    query: str,
    *,
    site_id: str | None = None,
    artifact_types: list[str] | None = None,
    top_k: int = 10,
) -> list[dict[str, Any]]:
    """Hybrid search across artifact collections."""
    query_vector = await embed_text(query)

    collections_to_search = []
    if artifact_types:
        for at in artifact_types:
            coll = COLLECTION_ARTIFACT_MAP.get(at)
            if coll:
                collections_to_search.append(coll)
    else:
        collections_to_search = list(COLLECTION_ARTIFACT_MAP.values())

    filters = None
    if site_id:
        filters = {"site_id": site_id}

    results = await hybrid_search(
        collections_to_search,
        query_vector,
        top_k_per_collection=max(3, top_k // len(collections_to_search)),
        filters=filters,
    )

    evidence = []
    seen_urls = set()
    for r in results:
        url = r.payload.get("source_url", "")
        if url and url in seen_urls:
            continue
        if url:
            seen_urls.add(url)
        evidence.append(
            {
                "score": r.score,
                "source_url": r.payload.get("source_url"),
                "artifact_type": r.payload.get("artifact_type"),
                "snippet": r.payload.get("chunk_text", "")[:500],
                "confidence": r.payload.get("confidence", 0.0),
                "title": r.payload.get("title"),
                "_collection": r.payload.get("_collection"),
                "site_id": r.payload.get("site_id"),
            }
        )
    return evidence

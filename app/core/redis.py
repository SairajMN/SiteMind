from __future__ import annotations

from typing import Any

import redis.asyncio as aioredis

from app.core.config import get_settings

_redis_client: aioredis.Redis | None = None


async def get_redis() -> aioredis.Redis:
    global _redis_client
    if _redis_client is None:
        settings = get_settings()
        _redis_client = aioredis.from_url(
            settings.redis_url,
            encoding="utf-8",
            decode_responses=True,
            socket_keepalive=True,
            health_check_interval=30,
            socket_connect_timeout=5,
        )
    return _redis_client


async def close_redis() -> None:
    global _redis_client
    if _redis_client is not None:
        await _redis_client.aclose()
        _redis_client = None


async def redis_ping() -> bool:
    client = await get_redis()
    return bool(await client.ping())


async def enqueue_job(queue: str, payload: dict[str, Any]) -> None:
    import json

    client = await get_redis()
    await client.lpush(queue, json.dumps(payload))

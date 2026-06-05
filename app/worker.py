"""Background worker — processes crawl jobs and runs site analysis DAG."""

from __future__ import annotations

import asyncio
import json
import logging
import uuid

import redis.asyncio as aioredis

from app.core.config import get_settings
from app.core.database import async_session_factory
from app.core.logging import setup_logging
from app.services.ingestion_service import WORKER_QUEUE
from app.services.site_dag_runner import run_site_dag

logger = logging.getLogger(__name__)


def _make_redis() -> aioredis.Redis:
    settings = get_settings()
    return aioredis.from_url(
        settings.redis_url,
        encoding="utf-8",
        decode_responses=True,
        socket_keepalive=True,
        health_check_interval=30,
        socket_connect_timeout=5,
    )


async def process_job(payload: dict) -> None:
    site_id = uuid.UUID(payload["site_id"])
    crawl_job_id = uuid.UUID(payload["crawl_job_id"])
    dag_run_id = uuid.UUID(payload["dag_run_id"])
    logger.info(
        "Processing crawl job site=%s job=%s dag=%s",
        site_id,
        crawl_job_id,
        dag_run_id,
    )
    async with async_session_factory() as session:
        try:
            summary = await run_site_dag(
                session,
                site_id=site_id,
                crawl_job_id=crawl_job_id,
                dag_run_id=dag_run_id,
            )
            logger.info("DAG completed: %s", summary)
        except Exception:
            await session.rollback()
            raise


async def poll_and_process(redis: aioredis.Redis) -> None:
    """Poll Redis using rpop (non-blocking) with short sleep."""
    while True:
        try:
            item = await redis.rpop(WORKER_QUEUE)
        except (ConnectionError, TimeoutError, OSError) as exc:
            logger.warning("Redis rpop failed: %s; reconnecting", exc)
            raise
        except Exception as exc:
            logger.warning("Redis rpop unexpected: %s; reconnecting", exc)
            raise

        if not item:
            await asyncio.sleep(0.5)
            continue

        try:
            payload = json.loads(item)
        except json.JSONDecodeError:
            logger.warning("Invalid job payload: %s", item)
            continue

        try:
            await process_job(payload)
        except Exception:
            logger.exception("Job failed: %s", payload.get("crawl_job_id"))


async def worker_loop() -> None:
    setup_logging()
    logger.info("SiteMind worker started")

    while True:
        redis = _make_redis()
        try:
            await redis.ping()
            logger.info("Worker connected to Redis")
            await poll_and_process(redis)
        except Exception as exc:
            logger.warning("Worker connection error: %s", exc)
        finally:
            try:
                await redis.aclose()
            except Exception:
                pass
        await asyncio.sleep(2.0)


def main() -> None:
    asyncio.run(worker_loop())


if __name__ == "__main__":
    main()

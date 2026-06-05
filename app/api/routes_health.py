from fastapi import APIRouter
from sqlalchemy import text

from app.core.database import engine
from app.core.redis import redis_ping
from app.schemas.common import ApiResponse

router = APIRouter(tags=["health"])


@router.get("/health")
async def health() -> ApiResponse[dict[str, str]]:
    return ApiResponse.ok({"status": "ok"})


@router.get("/health/ready")
async def readiness() -> ApiResponse[dict[str, bool]]:
    db_ok = False
    redis_ok = False
    try:
        async with engine.connect() as conn:
            await conn.execute(text("SELECT 1"))
        db_ok = True
    except Exception:
        db_ok = False
    try:
        redis_ok = await redis_ping()
    except Exception:
        redis_ok = False
    ready = db_ok and redis_ok
    return ApiResponse.ok({"ready": ready, "database": db_ok, "redis": redis_ok})

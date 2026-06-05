from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware

from app.api import (
    routes_api_specs,
    routes_dag,
    routes_endpoints,
    routes_evaluations,
    routes_forms,
    routes_health,
    routes_jobs,
    routes_pages,
    routes_qa,
    routes_sites,
    routes_workflows,
)
from app.core.config import get_settings
from app.core.database import engine
from app.core.logging import setup_logging
from app.core.qdrant import close_qdrant
from app.core.rate_limit import limiter
from app.core.redis import close_redis
from app.services.embedding_service import close_embedding_client
from app.schemas.common import ApiResponse


@asynccontextmanager
async def lifespan(app: FastAPI):
    setup_logging()
    yield
    await engine.dispose()
    await close_redis()
    await close_qdrant()
    await close_embedding_client()


def create_app() -> FastAPI:
    settings = get_settings()
    app = FastAPI(title=settings.app_name, lifespan=lifespan, debug=settings.debug)

    app.state.limiter = limiter

    @app.exception_handler(RateLimitExceeded)
    async def rate_limit_handler(request: Request, exc: RateLimitExceeded) -> JSONResponse:
        body = ApiResponse.fail(
            code="RATE_LIMITED",
            message="Too many requests",
            details={"retry_after": getattr(exc, "detail", None)},
        )
        return JSONResponse(status_code=429, content=body.model_dump())

    @app.exception_handler(Exception)
    async def unhandled_exception_handler(request: Request, exc: Exception) -> JSONResponse:
        if settings.debug:
            message = str(exc)
        else:
            message = "An unexpected error occurred"
        body = ApiResponse.fail(code="INTERNAL_ERROR", message=message)
        return JSONResponse(
            status_code=500,
            content=body.model_dump(),
            headers={
                "Access-Control-Allow-Origin": ",".join(settings.cors_origin_list),
                "Access-Control-Allow-Credentials": "true",
            },
        )

    app.add_middleware(SlowAPIMiddleware)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origin_list,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.include_router(routes_health.router, prefix="/api")
    app.include_router(routes_sites.router, prefix="/api")
    app.include_router(routes_jobs.router, prefix="/api")
    app.include_router(routes_pages.router, prefix="/api")
    app.include_router(routes_forms.router, prefix="/api")
    app.include_router(routes_endpoints.router, prefix="/api")
    app.include_router(routes_workflows.router, prefix="/api")
    app.include_router(routes_qa.router, prefix="/api")
    app.include_router(routes_api_specs.router, prefix="/api")
    app.include_router(routes_evaluations.router, prefix="/api")
    app.include_router(routes_dag.router, prefix="/api")

    return app


app = create_app()


def run() -> None:
    import uvicorn

    settings = get_settings()
    uvicorn.run(
        "app.main:app",
        host=settings.api_host,
        port=settings.api_port,
        reload=settings.debug,
    )


if __name__ == "__main__":
    run()
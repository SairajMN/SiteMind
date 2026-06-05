from functools import lru_cache
from typing import Literal

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    app_name: str = "SiteMind API"
    app_env: Literal["development", "staging", "production"] = "development"
    debug: bool = False
    log_level: str = "INFO"
    api_host: str = "0.0.0.0"
    api_port: int = 8000

    secret_key: str = Field(default="change-me", min_length=8)
    allow_localhost_targets: bool = False
    cors_origins: str = "http://localhost:3000"

    rate_limit_default: int = 60
    rate_limit_sites_post: int = 5
    rate_limit_ask: int = 10

    crawl_max_depth: int = 5
    crawl_max_page_budget: int = 200
    crawl_default_page_budget: int = 60
    crawl_default_depth: int = 3

    database_url: str = "postgresql+asyncpg://sitemind:sitemind@localhost:5432/sitemind"
    redis_url: str = "redis://localhost:6379/0"
    qdrant_url: str = "http://localhost:6333"
    qdrant_collection: str = "sitemind_chunks"

    groq_api_key: str | None = None
    openrouter_api_key: str | None = None
    inception_api_key: str | None = None
    default_llm_provider: str = "groq"

    @field_validator("cors_origins", mode="before")
    @classmethod
    def split_cors(cls, value: str | list[str]) -> str:
        if isinstance(value, list):
            return ",".join(value)
        return value

    @property
    def cors_origin_list(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()

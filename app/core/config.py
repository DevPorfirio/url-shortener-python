from functools import lru_cache
from typing import Any

from pydantic import AnyUrl, Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "URL Shortener API"
    app_env: str = "development"
    app_debug: bool = True
    api_v1_prefix: str = "/api/v1"

    secret_key: str = Field(
        "change-this-secret-key-change-this",
        min_length=32,
        alias="SECRET_KEY",
    )
    algorithm: str = "HS256"
    access_token_expires_minutes: int = 30
    refresh_token_expires_minutes: int = 43200

    mongodb_uri: AnyUrl = Field(..., alias="MONGODB_URI")
    mongodb_database: str = Field("url_shortener", alias="MONGODB_DATABASE")
    mongodb_user_collection: str = Field("users", alias="MONGODB_USER_COLLECTION")
    mongodb_url_collection: str = Field("urls", alias="MONGODB_URL_COLLECTION")
    mongodb_click_collection: str = Field("click_events", alias="MONGODB_CLICK_COLLECTION")

    redis_uri: AnyUrl = Field(..., alias="REDIS_URI")
    redis_cache_ttl_seconds: int = Field(3600, alias="REDIS_CACHE_TTL_SECONDS")

    celery_broker_url: AnyUrl = Field(..., alias="CELERY_BROKER_URL")
    celery_result_backend: AnyUrl = Field(..., alias="CELERY_RESULT_BACKEND")
    celery_default_queue: str = Field("shortener_tasks", alias="CELERY_TASK_DEFAULT_QUEUE")

    rate_limit_requests: int = Field(100, alias="RATE_LIMIT_REQUESTS")
    rate_limit_window_seconds: int = Field(60, alias="RATE_LIMIT_WINDOW_SECONDS")

    log_level: str = Field("INFO", alias="LOG_LEVEL")

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="allow",
        case_sensitive=False,
    )

    @property
    def is_production(self) -> bool:
        return self.app_env.lower() == "production"

    @property
    def mongo_database_settings(self) -> dict[str, Any]:
        return {
            "base": self.mongodb_database,
            "users": self.mongodb_user_collection,
            "urls": self.mongodb_url_collection,
            "clicks": self.mongodb_click_collection,
        }


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()

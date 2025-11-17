from fastapi import FastAPI
from redis.asyncio import Redis

from app.core.config import settings

REDIS_STATE_KEY = "redis"


async def connect_to_redis(app: FastAPI) -> None:
    redis = Redis.from_url(str(settings.redis_uri), encoding="utf-8", decode_responses=True)
    app.state.redis = redis


async def close_redis_connection(app: FastAPI) -> None:
    redis: Redis | None = getattr(app.state, REDIS_STATE_KEY, None)
    if redis:
        await redis.close()
        delattr(app.state, REDIS_STATE_KEY)


def get_redis_from_state(app: FastAPI) -> Redis:
    redis: Redis | None = getattr(app.state, REDIS_STATE_KEY, None)
    if not redis:
        raise RuntimeError("Redis connection is not initialized")
    return redis

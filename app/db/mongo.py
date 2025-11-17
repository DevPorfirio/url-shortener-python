from collections.abc import Callable

from fastapi import FastAPI
from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase

from app.core.config import settings

MONGO_CLIENT_STATE_KEY = "mongo_client"
MONGO_DB_STATE_KEY = "mongo_db"


async def connect_to_mongo(app: FastAPI) -> None:
    client = AsyncIOMotorClient(str(settings.mongodb_uri), tz_aware=True)
    database = client[settings.mongodb_database]
    app.state.mongo_client = client
    app.state.mongo_db = database


async def close_mongo_connection(app: FastAPI) -> None:
    client: AsyncIOMotorClient | None = getattr(app.state, MONGO_CLIENT_STATE_KEY, None)
    if client:
        client.close()
        delattr(app.state, MONGO_CLIENT_STATE_KEY)
    if hasattr(app.state, MONGO_DB_STATE_KEY):
        delattr(app.state, MONGO_DB_STATE_KEY)


def get_database_from_state(app: FastAPI) -> AsyncIOMotorDatabase:
    database: AsyncIOMotorDatabase | None = getattr(app.state, MONGO_DB_STATE_KEY, None)
    if database is None:
        raise RuntimeError("MongoDB connection is not initialized")
    return database


def mongo_dependency(app: FastAPI) -> Callable[[], AsyncIOMotorDatabase]:
    def get_db() -> AsyncIOMotorDatabase:
        return get_database_from_state(app)

    return get_db

import asyncio

from fastapi import FastAPI

from app.core.config import settings
from app.db.mongo import get_database_from_state


async def ensure_indexes(app: FastAPI) -> None:
    database = get_database_from_state(app)
    db_config = settings.mongo_database_settings

    users = database[db_config["users"]]
    urls = database[db_config["urls"]]
    clicks = database[db_config["clicks"]]

    await asyncio.gather(
        users.create_index("email", unique=True, name="ix_users_email_unique"),
        urls.create_index("short_code", unique=True, name="ix_urls_short_code_unique"),
        urls.create_index(
            [
                ("owner_id", 1),
                ("short_code", 1),
            ],
            unique=True,
            name="ix_urls_owner_short_code_unique",
        ),
        urls.create_index(
            "expires_at",
            expireAfterSeconds=0,
            partialFilterExpression={"expires_at": {"$exists": True}},
            name="ix_urls_expiration",
        ),
        clicks.create_index("short_code", name="ix_clicks_short_code"),
        clicks.create_index("created_at", name="ix_clicks_created_at"),
    )

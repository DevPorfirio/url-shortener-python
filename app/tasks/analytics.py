from datetime import UTC, datetime

from pymongo import MongoClient

from app.core.config import settings
from app.tasks.celery_app import celery_app


def _get_client() -> MongoClient:
    return MongoClient(str(settings.mongodb_uri))


@celery_app.task(name="analytics.log_click")
def log_click_event(short_code: str) -> None:
    client = _get_client()
    try:
        database = client[settings.mongodb_database]
        clicks_collection = database[settings.mongo_database_settings["clicks"]]
        urls_collection = database[settings.mongo_database_settings["urls"]]

        now = datetime.now(UTC)
        clicks_collection.insert_one(
            {
                "short_code": short_code,
                "created_at": now,
            }
        )
        urls_collection.update_one(
            {"short_code": short_code},
            {
                "$inc": {"click_count": 1},
                "$set": {"last_clicked_at": now, "updated_at": now},
            },
        )
    finally:  # pragma: no branch - always executes
        client.close()

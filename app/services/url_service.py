from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from typing import Any

from bson import ObjectId
from motor.motor_asyncio import AsyncIOMotorCollection, AsyncIOMotorDatabase
from redis.asyncio import Redis

from app.core.logging import get_logger
from app.schemas.url import URLAnalytics, URLCreate, URLRead, URLWithAnalytics
from app.utils.id_generator import generate_short_code
from app.utils.time import utc_now

logger = get_logger(__name__)


@dataclass(slots=True)
class UrlServiceConfig:
    cache_ttl_seconds: int
    url_collection: str
    click_collection: str


class UrlService:
    def __init__(
        self,
        database: AsyncIOMotorDatabase,
        redis: Redis,
        config: UrlServiceConfig,
    ) -> None:
        self._database = database
        self._redis = redis
        self._url_collection: AsyncIOMotorCollection = database[config.url_collection]
        self._click_collection: AsyncIOMotorCollection = database[config.click_collection]
        self._config = config

    async def create_short_url(self, payload: URLCreate, owner_id: str) -> URLRead:
        short_code = await self._ensure_unique_short_code(payload.custom_alias)
        now = utc_now()
        expires_at = (
            now + timedelta(seconds=payload.expires_in_seconds)
            if payload.expires_in_seconds
            else None
        )
        owner_ref = self._to_object_id(owner_id)

        doc: dict[str, Any] = {
            "short_code": short_code,
            "target_url": str(payload.target_url),
            "owner_id": owner_ref,
            "expires_at": expires_at,
            "created_at": now,
            "updated_at": now,
        }
        result = await self._url_collection.insert_one(doc)
        doc["_id"] = result.inserted_id
        await self._cache_target(short_code, doc["target_url"], expires_at)
        return self._document_to_schema(doc, short_url="")

    async def list_urls(self, owner_id: str, limit: int = 100, skip: int = 0) -> list[URLRead]:
        owner_ref = self._to_object_id(owner_id)
        cursor = (
            self._url_collection.find({"owner_id": owner_ref})
            .sort("created_at", -1)
            .skip(skip)
            .limit(limit)
        )
        items = [self._document_to_schema(doc, short_url="") async for doc in cursor]
        return items

    async def delete_url(self, owner_id: str, short_code: str) -> bool:
        owner_ref = self._to_object_id(owner_id)
        result = await self._url_collection.delete_one(
            {"owner_id": owner_ref, "short_code": short_code}
        )
        await self._redis.delete(self._cache_key(short_code))
        return result.deleted_count > 0

    async def resolve_short_code(self, short_code: str) -> str | None:
        cache_key = self._cache_key(short_code)
        cached_target = await self._redis.get(cache_key)
        if cached_target:
            self._enqueue_click(short_code)
            return cached_target

        doc = await self._url_collection.find_one({"short_code": short_code})
        if not doc:
            return None

        expires_at: datetime | None = doc.get("expires_at")
        if expires_at and expires_at <= datetime.now(UTC):
            await self._redis.delete(cache_key)
            return None

        target_url = doc.get("target_url")
        await self._cache_target(short_code, target_url, expires_at)
        self._enqueue_click(short_code)
        return target_url

    async def get_url_with_analytics(self, owner_id: str, short_code: str) -> URLWithAnalytics | None:
        owner_ref = self._to_object_id(owner_id)
        doc = await self._url_collection.find_one(
            {"owner_id": owner_ref, "short_code": short_code}
        )
        if not doc:
            return None
        analytics = await self._build_analytics(short_code)
        url_schema = self._document_to_schema(doc, short_url="")
        return URLWithAnalytics(**url_schema.model_dump(), analytics=analytics)

    async def refresh_cache(self, short_code: str) -> None:
        doc = await self._url_collection.find_one({"short_code": short_code})
        if not doc:
            return
        await self._cache_target(
            short_code,
            doc.get("target_url"),
            doc.get("expires_at"),
        )

    async def _ensure_unique_short_code(self, requested_alias: str | None) -> str:
        if requested_alias:
            exists = await self._url_collection.find_one({"short_code": requested_alias})
            if exists:
                raise ValueError("Custom alias already in use")
            return requested_alias

        for _ in range(5):
            candidate = generate_short_code()
            exists = await self._url_collection.find_one({"short_code": candidate})
            if not exists:
                return candidate
        raise RuntimeError("Unable to generate unique short code, try again")

    async def _cache_target(
        self,
        short_code: str,
        target_url: str,
        expires_at: datetime | None,
    ) -> None:
        ttl = self._config.cache_ttl_seconds
        if expires_at:
            ttl = max(0, int((expires_at - datetime.now(UTC)).total_seconds()))
        if ttl <= 0:
            await self._redis.delete(self._cache_key(short_code))
            return
        await self._redis.setex(self._cache_key(short_code), ttl, target_url)

    async def _build_analytics(self, short_code: str) -> URLAnalytics:
        total_clicks = await self._click_collection.count_documents({"short_code": short_code})
        last_click = await self._click_collection.find_one(
            {"short_code": short_code}, sort=[("created_at", -1)]
        )
        analytics = URLAnalytics(
            short_code=short_code,
            total_clicks=total_clicks,
            last_clicked_at=last_click.get("created_at") if last_click else None,
            unique_visitors=None,
        )
        return analytics

    def _document_to_schema(self, doc: dict[str, Any], short_url: str) -> URLRead:
        object_id = doc.get("_id")
        if object_id is None:
            raise ValueError("Document missing identifier")
        short_code = str(doc.get("short_code"))
        target_url = str(doc.get("target_url"))
        owner_value = doc.get("owner_id")
        owner_str = str(owner_value)

        data: dict[str, Any] = {
            "id": str(object_id),
            "short_code": short_code,
            "short_url": short_url or short_code,
            "target_url": target_url,
            "owner_id": owner_str,
            "expires_at": self._normalize_datetime(doc.get("expires_at")) if doc.get("expires_at") else None,
            "created_at": self._normalize_datetime(doc.get("created_at")),
            "updated_at": self._normalize_datetime(doc.get("updated_at")),
        }
        return URLRead.model_validate(data)

    def _cache_key(self, short_code: str) -> str:
        return f"url:{short_code}"

    def _enqueue_click(self, short_code: str) -> None:
        try:
            from app.tasks.analytics import log_click_event

            log_click_event.delay(short_code)
        except Exception as exc:  # pragma: no cover - best effort logging
            logger.warning("failed to enqueue click event", short_code=short_code, error=str(exc))

    def _to_object_id(self, value: str) -> ObjectId:
        if not ObjectId.is_valid(value):
            raise ValueError("Invalid owner identifier")
        return ObjectId(value)

    def _normalize_datetime(self, value: Any) -> datetime:
        if isinstance(value, datetime):
            return value if value.tzinfo else value.replace(tzinfo=UTC)
        if value is None:
            return utc_now()
        try:
            parsed = datetime.fromisoformat(str(value))
        except ValueError:
            return utc_now()
        return parsed if parsed.tzinfo else parsed.replace(tzinfo=UTC)

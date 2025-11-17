from datetime import UTC, datetime
from typing import Any

from bson import ObjectId
from motor.motor_asyncio import AsyncIOMotorCollection, AsyncIOMotorDatabase

from app.core.security import hash_password, verify_password
from app.schemas.user import UserCreate, UserInDB
from app.utils.time import utc_now


class UserService:
    def __init__(self, database: AsyncIOMotorDatabase, collection_name: str) -> None:
        self.collection: AsyncIOMotorCollection = database[collection_name]

    async def create_user(self, data: UserCreate) -> UserInDB:
        existing = await self.collection.find_one({"email": data.email})
        if existing:
            raise ValueError("Email already registered")

        now = utc_now()
        doc: dict[str, Any] = {
            "email": data.email,
            "hashed_password": hash_password(data.password),
            "is_active": True,
            "created_at": now,
            "updated_at": now,
        }
        result = await self.collection.insert_one(doc)
        doc["_id"] = result.inserted_id
        return self._document_to_user(doc)

    async def authenticate_user(self, email: str, password: str) -> UserInDB | None:
        doc = await self.collection.find_one({"email": email})
        if not doc:
            return None
        user = self._document_to_user(doc)
        if not verify_password(password, user.hashed_password):
            return None
        return user

    async def get_user_by_id(self, user_id: str) -> UserInDB | None:
        if not ObjectId.is_valid(user_id):
            return None
        doc = await self.collection.find_one({"_id": ObjectId(user_id)})
        if not doc:
            return None
        return self._document_to_user(doc)

    async def get_user_by_email(self, email: str) -> UserInDB | None:
        doc = await self.collection.find_one({"email": email})
        if not doc:
            return None
        return self._document_to_user(doc)

    async def set_last_login(self, user_id: str) -> None:
        if not ObjectId.is_valid(user_id):
            return
        now = utc_now()
        await self.collection.update_one(
            {"_id": ObjectId(user_id)},
            {"$set": {"last_login_at": now, "updated_at": now}},
        )

    def _document_to_user(self, doc: dict[str, Any]) -> UserInDB:
        payload = {
            "id": str(doc["_id"]),
            "email": doc["email"],
            "hashed_password": doc["hashed_password"],
            "is_active": doc.get("is_active", True),
            "created_at": self._ensure_datetime(doc.get("created_at")),
            "updated_at": self._ensure_datetime(doc.get("updated_at")),
        }
        return UserInDB(**payload)

    def _ensure_datetime(self, value: Any) -> datetime:
        if isinstance(value, datetime):
            return value if value.tzinfo else value.replace(tzinfo=UTC)
        if not value:
            return utc_now()
        try:
            parsed = datetime.fromisoformat(str(value))
        except ValueError:
            return utc_now()
        return parsed if parsed.tzinfo else parsed.replace(tzinfo=UTC)

from datetime import datetime

from pydantic import AnyUrl, Field

from app.schemas.common import MongoModel, PyObjectId


class URLBase(MongoModel):
    target_url: AnyUrl


class URLCreate(URLBase):
    custom_alias: str | None = Field(default=None, min_length=4, max_length=32)
    expires_in_seconds: int | None = Field(default=None, ge=60, le=31536000)


class URLUpdate(MongoModel):
    target_url: AnyUrl | None = None
    expires_in_seconds: int | None = Field(default=None, ge=60, le=31536000)


class URLRead(URLBase):
    id: PyObjectId = Field(alias="id")
    short_code: str
    short_url: str
    owner_id: PyObjectId
    expires_at: datetime | None = None
    created_at: datetime
    updated_at: datetime


class URLAnalytics(MongoModel):
    short_code: str
    total_clicks: int
    unique_visitors: int | None = None
    last_clicked_at: datetime | None = None


class URLWithAnalytics(URLRead):
    analytics: URLAnalytics | None = None

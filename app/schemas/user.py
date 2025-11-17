from datetime import datetime

from pydantic import EmailStr, Field

from app.schemas.common import MongoModel, PyObjectId


class UserBase(MongoModel):
    email: EmailStr


class UserCreate(UserBase):
    password: str = Field(min_length=8, max_length=128)


class UserLogin(UserBase):
    password: str = Field(min_length=8, max_length=128)


class UserRead(UserBase):
    id: PyObjectId = Field(alias="id")
    is_active: bool
    created_at: datetime
    updated_at: datetime


class UserInDB(UserRead):
    hashed_password: str

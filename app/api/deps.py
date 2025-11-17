from fastapi import Depends, HTTPException, Request, status
from fastapi.security import OAuth2PasswordBearer
from motor.motor_asyncio import AsyncIOMotorDatabase
from redis.asyncio import Redis

from app.core.config import settings
from app.db.mongo import get_database_from_state
from app.db.redis import get_redis_from_state
from app.schemas.user import UserInDB
from app.services.token_service import TokenService
from app.services.url_service import UrlService, UrlServiceConfig
from app.services.user_service import UserService

oauth2_scheme = OAuth2PasswordBearer(tokenUrl=f"{settings.api_v1_prefix}/auth/login")
_token_service = TokenService()


async def get_mongo_db(request: Request) -> AsyncIOMotorDatabase:
    return get_database_from_state(request.app)


async def get_redis(request: Request) -> Redis:
    return get_redis_from_state(request.app)


async def get_user_service(db: AsyncIOMotorDatabase = Depends(get_mongo_db)) -> UserService:
    return UserService(db, settings.mongo_database_settings["users"])


async def get_url_service(
    db: AsyncIOMotorDatabase = Depends(get_mongo_db),
    redis: Redis = Depends(get_redis),
) -> UrlService:
    config = UrlServiceConfig(
        cache_ttl_seconds=settings.redis_cache_ttl_seconds,
        url_collection=settings.mongo_database_settings["urls"],
        click_collection=settings.mongo_database_settings["clicks"],
    )
    return UrlService(db, redis, config)


async def get_current_user(
    token: str = Depends(oauth2_scheme),
    user_service: UserService = Depends(get_user_service),
) -> UserInDB:
    try:
        payload = _token_service.verify_token(token)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        ) from exc

    user = await user_service.get_user_by_id(payload.sub)
    if not user or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Inactive or missing user",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return user


def get_token_service() -> TokenService:
    return _token_service

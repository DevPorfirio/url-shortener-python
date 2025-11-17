from contextlib import asynccontextmanager

from fastapi import Depends, FastAPI, HTTPException
from fastapi.responses import RedirectResponse

from app.api import deps
from app.api.router import api_router
from app.core.config import settings
from app.core.logging import configure_logging
from app.db.indexes import ensure_indexes
from app.db.mongo import close_mongo_connection, connect_to_mongo
from app.db.redis import close_redis_connection, connect_to_redis
from app.services.url_service import UrlService


@asynccontextmanager
async def lifespan(app: FastAPI):
    configure_logging()
    await connect_to_mongo(app)
    await connect_to_redis(app)
    await ensure_indexes(app)
    try:
        yield
    finally:
        await close_redis_connection(app)
        await close_mongo_connection(app)


def create_application() -> FastAPI:
    application = FastAPI(
        title=settings.app_name,
        version="0.1.0",
        lifespan=lifespan,
    )

    application.include_router(api_router, prefix=settings.api_v1_prefix)
    return application


app = create_application()


@app.get("/{short_code}", include_in_schema=False)
async def redirect_short_url(
    short_code: str,
    url_service: UrlService = Depends(deps.get_url_service),
):
    target = await url_service.resolve_short_code(short_code)
    if not target:
        raise HTTPException(status_code=404, detail="Short URL not found")
    return RedirectResponse(target, status_code=307)

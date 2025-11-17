from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status

from app.api import deps
from app.schemas.url import URLCreate, URLRead, URLWithAnalytics
from app.schemas.user import UserInDB
from app.services.url_service import UrlService

router = APIRouter()


def _build_short_url(request: Request, short_code: str) -> str:
    base_url = str(request.base_url).rstrip("/")
    return f"{base_url}/{short_code}"


def _attach_short_url(request: Request, url: URLRead) -> URLRead:
    return url.model_copy(update={"short_url": _build_short_url(request, url.short_code)})


@router.post("/", response_model=URLRead, status_code=status.HTTP_201_CREATED)
async def create_short_url(
    payload: URLCreate,
    request: Request,
    current_user: Annotated[UserInDB, Depends(deps.get_current_user)],
    url_service: Annotated[UrlService, Depends(deps.get_url_service)],
) -> URLRead:
    try:
        created = await url_service.create_short_url(payload, current_user.id)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    return _attach_short_url(request, created)


@router.get("/", response_model=list[URLRead])
async def list_short_urls(
    request: Request,
    current_user: Annotated[UserInDB, Depends(deps.get_current_user)],
    url_service: Annotated[UrlService, Depends(deps.get_url_service)],
    limit: int = Query(default=100, ge=1, le=500),
    skip: int = Query(default=0, ge=0),
) -> list[URLRead]:
    try:
        urls = await url_service.list_urls(current_user.id, limit=limit, skip=skip)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    return [_attach_short_url(request, item) for item in urls]


@router.get("/{short_code}", response_model=URLWithAnalytics)
async def get_short_url(
    short_code: str,
    request: Request,
    current_user: Annotated[UserInDB, Depends(deps.get_current_user)],
    url_service: Annotated[UrlService, Depends(deps.get_url_service)],
) -> URLWithAnalytics:
    try:
        url = await url_service.get_url_with_analytics(current_user.id, short_code)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    if not url:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Short URL not found")
    return url.model_copy(update={"short_url": _build_short_url(request, short_code)})


@router.delete("/{short_code}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_short_url(
    short_code: str,
    current_user: Annotated[UserInDB, Depends(deps.get_current_user)],
    url_service: Annotated[UrlService, Depends(deps.get_url_service)],
) -> None:
    try:
        deleted = await url_service.delete_url(current_user.id, short_code)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    if not deleted:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Short URL not found")

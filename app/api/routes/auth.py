from fastapi import APIRouter, Depends, HTTPException, status

from app.api import deps
from app.schemas.auth import Token, TokenRefreshRequest
from app.schemas.user import UserCreate, UserInDB, UserLogin, UserRead
from app.services.token_service import TokenService
from app.services.user_service import UserService

router = APIRouter()


@router.post("/register", response_model=UserRead, status_code=status.HTTP_201_CREATED)
async def register_user(
    payload: UserCreate,
    user_service: UserService = Depends(deps.get_user_service),
) -> UserRead:
    try:
        user = await user_service.create_user(payload)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    return UserRead.model_validate(user.model_dump(exclude={"hashed_password"}))


@router.post("/login", response_model=Token)
async def login_user(
    credentials: UserLogin,
    user_service: UserService = Depends(deps.get_user_service),
    token_service: TokenService = Depends(deps.get_token_service),
) -> Token:
    user = await user_service.authenticate_user(credentials.email, credentials.password)
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")

    access_token, refresh_token = token_service.create_tokens(user.id)
    await user_service.set_last_login(user.id)
    return Token(access_token=access_token, refresh_token=refresh_token)


@router.get("/me", response_model=UserRead)
async def read_current_user(current_user: UserInDB = Depends(deps.get_current_user)) -> UserRead:
    return UserRead.model_validate(current_user.model_dump(exclude={"hashed_password"}))


@router.post("/refresh", response_model=Token)
async def refresh_token(
    payload: TokenRefreshRequest,
    token_service: TokenService = Depends(deps.get_token_service),
) -> Token:
    try:
        token_payload = token_service.verify_token(payload.refresh_token, expected_type="refresh")
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid refresh token") from exc

    access_token, refresh_token = token_service.create_tokens(token_payload.sub)
    return Token(access_token=access_token, refresh_token=refresh_token)

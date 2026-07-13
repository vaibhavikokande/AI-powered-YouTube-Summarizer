from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user
from app.db.session import get_db
from app.models.user import User
from app.schemas.auth import GoogleLoginRequest, RefreshRequest, Token, UserLogin
from app.schemas.user import UserCreate, UserResponse
from app.services.auth_service import AuthService

router = APIRouter(tags=["auth"])


@router.post("/register", response_model=Token)
async def register(request: UserCreate, db: AsyncSession = Depends(get_db)) -> Token:
    service = AuthService(db)
    user = await service.register(request.email, request.password, request.full_name)
    return service.issue_tokens(user)


@router.post("/login", response_model=Token)
async def login(request: UserLogin, db: AsyncSession = Depends(get_db)) -> Token:
    service = AuthService(db)
    user = await service.authenticate(request.email, request.password)
    return service.issue_tokens(user)


@router.post("/login/google", response_model=Token)
async def login_with_google(request: GoogleLoginRequest, db: AsyncSession = Depends(get_db)) -> Token:
    service = AuthService(db)
    user = await service.login_with_google(request.id_token)
    return service.issue_tokens(user)


@router.post("/refresh", response_model=Token)
async def refresh_token(request: RefreshRequest, db: AsyncSession = Depends(get_db)) -> Token:
    return await AuthService(db).refresh(request.refresh_token)


@router.get("/me", response_model=UserResponse)
async def get_me(current_user: User = Depends(get_current_user)) -> UserResponse:
    return current_user

import uuid

from jose import JWTError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import UnauthorizedError, ValidationAppError
from app.core.security import (
    create_access_token,
    create_refresh_token,
    decode_token,
    hash_password,
    verify_password,
)
from app.models.user import User
from app.repositories.user_repository import UserRepository
from app.schemas.auth import Token
from app.services.google_oauth_service import GoogleOAuthService


class AuthService:
    def __init__(self, session: AsyncSession, google_oauth: GoogleOAuthService | None = None):
        self._repository = UserRepository(session)
        self._google_oauth = google_oauth or GoogleOAuthService()

    async def register(self, email: str, password: str, full_name: str | None) -> User:
        existing = await self._repository.get_by_email(email)
        if existing is not None:
            raise ValidationAppError("An account with this email already exists.")
        return await self._repository.create(
            email, hashed_password=hash_password(password), full_name=full_name
        )

    async def authenticate(self, email: str, password: str) -> User:
        user = await self._repository.get_by_email(email)
        if user is None or user.hashed_password is None:
            raise UnauthorizedError("Incorrect email or password.")
        if not verify_password(password, user.hashed_password):
            raise UnauthorizedError("Incorrect email or password.")
        if not user.is_active:
            raise UnauthorizedError("This account has been deactivated.")
        return user

    async def login_with_google(self, id_token: str) -> User:
        claims = await self._google_oauth.verify_id_token(id_token)
        google_id = claims["sub"]
        email = claims.get("email")

        user = await self._repository.get_by_google_id(google_id)
        if user is not None:
            return user

        # First Google login for this email — link to an existing
        # password-based account if one exists, otherwise create a new one.
        if email:
            existing = await self._repository.get_by_email(email)
            if existing is not None:
                return existing

        return await self._repository.create(
            email or f"{google_id}@google-oauth.invalid",
            google_id=google_id,
            full_name=claims.get("name"),
            avatar_url=claims.get("picture"),
        )

    def issue_tokens(self, user: User) -> Token:
        return Token(
            access_token=create_access_token(str(user.id)),
            refresh_token=create_refresh_token(str(user.id)),
        )

    async def refresh(self, refresh_token: str) -> Token:
        try:
            payload = decode_token(refresh_token)
        except JWTError as exc:
            raise UnauthorizedError("Invalid or expired refresh token.") from exc

        if payload.get("type") != "refresh":
            raise UnauthorizedError("Token is not a refresh token.")

        user = await self._repository.get_by_id(uuid.UUID(payload["sub"]))
        if user is None or not user.is_active:
            raise UnauthorizedError("User not found or inactive.")

        return self.issue_tokens(user)

import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User


class UserRepository:
    def __init__(self, session: AsyncSession):
        self._session = session

    async def get_by_id(self, user_id: uuid.UUID) -> User | None:
        return await self._session.get(User, user_id)

    async def get_by_email(self, email: str) -> User | None:
        result = await self._session.execute(select(User).where(User.email == email))
        return result.scalar_one_or_none()

    async def get_by_google_id(self, google_id: str) -> User | None:
        result = await self._session.execute(select(User).where(User.google_id == google_id))
        return result.scalar_one_or_none()

    async def create(
        self,
        email: str,
        *,
        hashed_password: str | None = None,
        google_id: str | None = None,
        full_name: str | None = None,
        avatar_url: str | None = None,
    ) -> User:
        user = User(
            email=email,
            hashed_password=hashed_password,
            google_id=google_id,
            full_name=full_name,
            avatar_url=avatar_url,
        )
        self._session.add(user)
        await self._session.commit()
        await self._session.refresh(user)
        return user

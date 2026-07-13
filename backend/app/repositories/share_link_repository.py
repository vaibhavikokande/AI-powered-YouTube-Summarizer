import secrets
import uuid
from datetime import datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.share_link import ShareLink


class ShareLinkRepository:
    def __init__(self, session: AsyncSession):
        self._session = session

    async def get_by_token(self, token: str) -> ShareLink | None:
        result = await self._session.execute(
            select(ShareLink).where(ShareLink.token == token).options(selectinload(ShareLink.summary))
        )
        return result.scalar_one_or_none()

    async def create(self, summary_id: uuid.UUID, expires_at: datetime | None = None) -> ShareLink:
        share_link = ShareLink(
            token=secrets.token_urlsafe(16), summary_id=summary_id, expires_at=expires_at
        )
        self._session.add(share_link)
        await self._session.commit()
        await self._session.refresh(share_link)
        return share_link

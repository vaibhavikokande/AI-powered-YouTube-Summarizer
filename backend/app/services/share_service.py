import uuid
from datetime import datetime, timezone

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import NotFoundError
from app.models.share_link import ShareLink
from app.models.summary import Summary
from app.repositories.share_link_repository import ShareLinkRepository
from app.repositories.summary_repository import SummaryRepository


class ShareService:
    def __init__(self, session: AsyncSession):
        self._share_repository = ShareLinkRepository(session)
        self._summary_repository = SummaryRepository(session)

    async def create_share_link(self, summary_id: uuid.UUID) -> ShareLink:
        summary = await self._summary_repository.get_by_id(summary_id)
        if summary is None:
            raise NotFoundError(f"Summary {summary_id} not found.")
        return await self._share_repository.create(summary_id)

    async def resolve_share_link(self, token: str) -> Summary:
        share_link = await self._share_repository.get_by_token(token)
        if share_link is None:
            raise NotFoundError("Share link not found.")
        if share_link.expires_at is not None and share_link.expires_at < datetime.now(timezone.utc):
            raise NotFoundError("This share link has expired.")
        return share_link.summary

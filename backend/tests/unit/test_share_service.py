import uuid
from datetime import datetime, timedelta, timezone
from unittest.mock import AsyncMock, MagicMock

import pytest

from app.core.exceptions import NotFoundError
from app.services.share_service import ShareService


def _service_with_mocks() -> ShareService:
    service = ShareService(session=MagicMock())
    service._share_repository = MagicMock()
    service._summary_repository = MagicMock()
    return service


async def test_create_share_link_raises_when_summary_not_found():
    service = _service_with_mocks()
    service._summary_repository.get_by_id = AsyncMock(return_value=None)

    with pytest.raises(NotFoundError):
        await service.create_share_link(uuid.uuid4())


async def test_create_share_link_creates_when_summary_exists():
    service = _service_with_mocks()
    service._summary_repository.get_by_id = AsyncMock(return_value=MagicMock())
    service._share_repository.create = AsyncMock(return_value="new-share-link")

    result = await service.create_share_link(uuid.uuid4())

    assert result == "new-share-link"


async def test_resolve_share_link_raises_when_token_not_found():
    service = _service_with_mocks()
    service._share_repository.get_by_token = AsyncMock(return_value=None)

    with pytest.raises(NotFoundError):
        await service.resolve_share_link("bad-token")


async def test_resolve_share_link_raises_when_expired():
    service = _service_with_mocks()
    expired_link = MagicMock()
    expired_link.expires_at = datetime.now(timezone.utc) - timedelta(days=1)
    service._share_repository.get_by_token = AsyncMock(return_value=expired_link)

    with pytest.raises(NotFoundError):
        await service.resolve_share_link("expired-token")


async def test_resolve_share_link_returns_summary_when_valid():
    service = _service_with_mocks()
    link = MagicMock()
    link.expires_at = None
    link.summary = "the-summary"
    service._share_repository.get_by_token = AsyncMock(return_value=link)

    result = await service.resolve_share_link("valid-token")

    assert result == "the-summary"

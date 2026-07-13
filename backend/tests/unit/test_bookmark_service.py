import uuid
from unittest.mock import AsyncMock, MagicMock

import pytest

from app.core.exceptions import ForbiddenError, NotFoundError
from app.schemas.favorite import BookmarkCreate
from app.services.bookmark_service import BookmarkService


def _service_with_mocks() -> BookmarkService:
    service = BookmarkService(session=MagicMock())
    service._repository = MagicMock()
    return service


async def test_add_bookmark_creates_via_repository():
    service = _service_with_mocks()
    service._repository.create = AsyncMock(return_value="new-bookmark")
    user_id = uuid.uuid4()
    data = BookmarkCreate(video_id=uuid.uuid4(), timestamp_seconds=42, note="key moment")

    result = await service.add_bookmark(user_id, data)

    assert result == "new-bookmark"
    service._repository.create.assert_called_once_with(
        user_id, data.video_id, 42, "key moment"
    )


async def test_remove_bookmark_raises_when_not_found():
    service = _service_with_mocks()
    service._repository.get = AsyncMock(return_value=None)

    with pytest.raises(NotFoundError):
        await service.remove_bookmark(uuid.uuid4(), uuid.uuid4())


async def test_remove_bookmark_raises_forbidden_for_other_users_bookmark():
    service = _service_with_mocks()
    bookmark = MagicMock()
    bookmark.user_id = uuid.uuid4()
    service._repository.get = AsyncMock(return_value=bookmark)

    with pytest.raises(ForbiddenError):
        await service.remove_bookmark(uuid.uuid4(), uuid.uuid4())


async def test_remove_bookmark_deletes_own_bookmark():
    service = _service_with_mocks()
    user_id = uuid.uuid4()
    bookmark = MagicMock()
    bookmark.user_id = user_id
    service._repository.get = AsyncMock(return_value=bookmark)
    service._repository.delete = AsyncMock()

    await service.remove_bookmark(user_id, uuid.uuid4())

    service._repository.delete.assert_called_once_with(bookmark)

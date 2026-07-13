import uuid
from unittest.mock import AsyncMock, MagicMock

import pytest

from app.core.exceptions import NotFoundError
from app.services.favorite_service import FavoriteService


def _service_with_mocks() -> FavoriteService:
    service = FavoriteService(session=MagicMock())
    service._repository = MagicMock()
    return service


async def test_add_favorite_returns_existing_without_duplicating():
    service = _service_with_mocks()
    existing = MagicMock()
    service._repository.get = AsyncMock(return_value=existing)
    service._repository.add = AsyncMock()

    result = await service.add_favorite(uuid.uuid4(), uuid.uuid4())

    assert result is existing
    service._repository.add.assert_not_called()


async def test_add_favorite_creates_when_not_already_favorited():
    service = _service_with_mocks()
    service._repository.get = AsyncMock(return_value=None)
    service._repository.add = AsyncMock(return_value="new-favorite")

    result = await service.add_favorite(uuid.uuid4(), uuid.uuid4())

    assert result == "new-favorite"


async def test_remove_favorite_raises_when_not_found():
    service = _service_with_mocks()
    service._repository.get = AsyncMock(return_value=None)

    with pytest.raises(NotFoundError):
        await service.remove_favorite(uuid.uuid4(), uuid.uuid4())


async def test_remove_favorite_deletes_existing():
    service = _service_with_mocks()
    existing = MagicMock()
    service._repository.get = AsyncMock(return_value=existing)
    service._repository.remove = AsyncMock()

    await service.remove_favorite(uuid.uuid4(), uuid.uuid4())

    service._repository.remove.assert_called_once_with(existing)

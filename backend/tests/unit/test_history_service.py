import uuid
from unittest.mock import AsyncMock, MagicMock

from app.services.history_service import HistoryService


def _service_with_mocks() -> HistoryService:
    service = HistoryService(session=MagicMock())
    service._repository = MagicMock()
    return service


async def test_record_view_delegates_to_repository_touch():
    service = _service_with_mocks()
    service._repository.touch = AsyncMock()
    user_id, video_id = uuid.uuid4(), uuid.uuid4()

    await service.record_view(user_id, video_id)

    service._repository.touch.assert_called_once_with(user_id, video_id)


async def test_list_history_delegates_to_repository_with_filters():
    service = _service_with_mocks()
    service._repository.list_by_user = AsyncMock(return_value=(["video"], 1))
    user_id = uuid.uuid4()

    videos, total = await service.list_history(user_id, search="python", limit=10, offset=5)

    assert videos == ["video"]
    assert total == 1
    service._repository.list_by_user.assert_called_once_with(
        user_id, search="python", limit=10, offset=5
    )

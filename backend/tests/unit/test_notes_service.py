import uuid
from unittest.mock import AsyncMock, MagicMock

from app.services.notes_service import NotesService


def _service_with_mocks() -> NotesService:
    llm = MagicMock()
    llm.generate_text = AsyncMock(return_value="## Notes\n- Point one")

    content_prep = MagicMock()
    content_prep.get_combined_summary = AsyncMock(return_value="combined summary")

    service = NotesService(session=MagicMock(), llm_provider=llm, content_prep=content_prep)
    service._repository = MagicMock()
    return service


def _fake_video():
    video = MagicMock()
    video.id = uuid.uuid4()
    video.title = "Test Video"
    return video


async def test_generate_returns_existing_note_without_llm_call():
    service = _service_with_mocks()
    existing = MagicMock()
    service._repository.get_by_video = AsyncMock(return_value=existing)

    result = await service.generate(_fake_video(), MagicMock())

    assert result is existing
    service._llm.generate_text.assert_not_called()


async def test_generate_creates_note_when_none_exists():
    service = _service_with_mocks()
    service._repository.get_by_video = AsyncMock(return_value=None)
    service._repository.create = AsyncMock(return_value="persisted note")

    result = await service.generate(_fake_video(), MagicMock())

    assert result == "persisted note"
    video_id, content_markdown = service._repository.create.call_args.args
    assert content_markdown == "## Notes\n- Point one"

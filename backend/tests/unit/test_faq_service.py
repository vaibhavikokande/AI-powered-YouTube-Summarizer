import uuid
from unittest.mock import AsyncMock, MagicMock

from app.schemas.faq import FAQList, FAQPair
from app.services.faq_service import FAQService


def _service_with_mocks() -> FAQService:
    llm = MagicMock()
    llm.generate_structured = AsyncMock(
        return_value=FAQList(items=[FAQPair(question="Q1?", answer="A1.")])
    )

    content_prep = MagicMock()
    content_prep.get_combined_summary = AsyncMock(return_value="combined summary")

    service = FAQService(session=MagicMock(), llm_provider=llm, content_prep=content_prep)
    service._repository = MagicMock()
    return service


def _fake_video():
    video = MagicMock()
    video.id = uuid.uuid4()
    return video


async def test_generate_returns_existing_faqs_without_llm_call():
    service = _service_with_mocks()
    existing = [MagicMock()]
    service._repository.list_by_video = AsyncMock(return_value=existing)

    result = await service.generate(_fake_video(), MagicMock())

    assert result == existing
    service._llm.generate_structured.assert_not_called()


async def test_generate_creates_faqs_when_none_exist():
    service = _service_with_mocks()
    service._repository.list_by_video = AsyncMock(return_value=[])
    service._repository.bulk_create = AsyncMock(return_value=["persisted"])

    result = await service.generate(_fake_video(), MagicMock(), count=1)

    assert result == ["persisted"]
    service._repository.bulk_create.assert_called_once()
    video_id, items = service._repository.bulk_create.call_args.args
    assert items == [("Q1?", "A1.")]

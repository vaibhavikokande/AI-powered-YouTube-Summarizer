import uuid
from unittest.mock import AsyncMock, MagicMock

from app.models.enums import SummaryType
from app.schemas.summary import KeyTakeaways, TimestampedSection, TimestampedSectionList, Topics
from app.services.summarization_service import SummarizationService


def _fake_video():
    video = MagicMock()
    video.id = uuid.uuid4()
    video.title = "Test Video"
    return video


def _fake_transcript():
    transcript = MagicMock()
    transcript.segments = [
        {"start": 0.0, "duration": 2.0, "text": "Hello world, this is a test."},
    ]
    return transcript


async def _fake_generate_structured(messages, schema):
    if schema is KeyTakeaways:
        return KeyTakeaways(important_concepts=["concept A"])
    if schema is Topics:
        return Topics(main_topics=["topic A"])
    if schema is TimestampedSectionList:
        return TimestampedSectionList(
            sections=[TimestampedSection(timestamp_seconds=0, title="Intro", summary="intro summary")]
        )
    raise AssertionError(f"unexpected schema: {schema}")


def _fake_llm():
    llm = MagicMock()
    llm.provider_name = "claude"
    llm.generate_text = AsyncMock(return_value="mock summary text")
    llm.generate_structured = AsyncMock(side_effect=_fake_generate_structured)
    return llm


def _service_with_mocks(llm=None):
    service = SummarizationService(session=MagicMock(), llm_provider=llm or _fake_llm())
    service._repository = MagicMock()
    return service


async def test_summarize_generates_and_persists_missing_types():
    service = _service_with_mocks()
    service._repository.get_by_video_and_type = AsyncMock(return_value=None)
    service._repository.create = AsyncMock(side_effect=lambda **kwargs: MagicMock(**kwargs))

    video = _fake_video()
    transcript = _fake_transcript()

    results = await service.summarize(
        video, transcript, summary_types=[SummaryType.SHORT, SummaryType.MEDIUM]
    )

    assert len(results) == 2
    assert service._repository.create.call_count == 2

    # Map step (1 chunk) + reduce step (2 requested types) = 3 generate_text calls.
    assert service._llm.generate_text.call_count == 3
    # key_takeaways + topics + timestamped_sections, regardless of summary type count.
    assert service._llm.generate_structured.call_count == 3

    created_types = [call.kwargs["summary_type"] for call in service._repository.create.call_args_list]
    assert created_types == [SummaryType.SHORT, SummaryType.MEDIUM]


async def test_summarize_skips_llm_entirely_when_all_types_already_exist():
    service = _service_with_mocks()
    existing_short = MagicMock()
    existing_medium = MagicMock()
    service._repository.get_by_video_and_type = AsyncMock(
        side_effect=[existing_short, existing_medium]
    )
    service._repository.create = AsyncMock()

    video = _fake_video()
    transcript = _fake_transcript()

    results = await service.summarize(
        video, transcript, summary_types=[SummaryType.SHORT, SummaryType.MEDIUM]
    )

    assert results == [existing_short, existing_medium]
    service._repository.create.assert_not_called()
    service._llm.generate_text.assert_not_called()
    service._llm.generate_structured.assert_not_called()

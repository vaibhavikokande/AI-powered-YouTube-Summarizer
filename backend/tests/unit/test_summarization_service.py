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
    transcript.id = uuid.uuid4()
    transcript.segments = [{"start": 0.0, "duration": 2.0, "text": "hello world"}]
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
    llm.generate_text = AsyncMock(return_value="mock generated text")
    llm.generate_structured = AsyncMock(side_effect=_fake_generate_structured)
    return llm


def _service_with_mocks(llm=None) -> SummarizationService:
    content_prep = MagicMock()
    content_prep.get_combined_summary = AsyncMock(return_value="combined summary text")
    content_prep.get_combined_summary_with_chunks = AsyncMock(
        return_value=("combined summary text", [MagicMock(start_seconds=0.0)], ["chunk summary"])
    )

    service = SummarizationService(
        session=MagicMock(), llm_provider=llm or _fake_llm(), content_prep=content_prep
    )
    service._repository = MagicMock()
    return service


async def test_first_summary_for_video_derives_and_persists_video_level_content():
    service = _service_with_mocks()
    service._repository.get_by_video_and_type = AsyncMock(return_value=None)
    service._repository.list_by_video = AsyncMock(return_value=[])
    service._repository.create = AsyncMock(side_effect=lambda **kwargs: MagicMock(**kwargs))

    results = await service.summarize(
        _fake_video(), _fake_transcript(), summary_types=[SummaryType.SHORT]
    )

    assert len(results) == 1
    service._content_prep.get_combined_summary_with_chunks.assert_called_once()
    service._content_prep.get_combined_summary.assert_not_called()
    # key_takeaways + topics + timestamped_sections = 3 structured calls, derived once.
    assert service._llm.generate_structured.call_count == 3
    service._repository.create.assert_called_once()


async def test_additional_summary_type_reuses_existing_video_level_content():
    service = _service_with_mocks()
    existing_summary = MagicMock()
    existing_summary.key_takeaways = {"important_concepts": ["existing concept"]}
    existing_summary.topics = {"main_topics": ["existing topic"]}
    existing_summary.timestamped_sections = [
        {"timestamp_seconds": 0, "title": "Intro", "summary": "intro"}
    ]

    service._repository.get_by_video_and_type = AsyncMock(return_value=None)
    service._repository.list_by_video = AsyncMock(return_value=[existing_summary])
    service._repository.create = AsyncMock(side_effect=lambda **kwargs: MagicMock(**kwargs))

    results = await service.summarize(
        _fake_video(), _fake_transcript(), summary_types=[SummaryType.MEDIUM]
    )

    assert len(results) == 1
    service._content_prep.get_combined_summary.assert_called_once()
    service._content_prep.get_combined_summary_with_chunks.assert_not_called()
    # Reused from the existing summary row instead of re-derived via the LLM.
    service._llm.generate_structured.assert_not_called()

    _, kwargs = service._repository.create.call_args
    assert kwargs["key_takeaways"] == {"important_concepts": ["existing concept"]}


async def test_summarize_skips_everything_when_all_types_already_exist():
    service = _service_with_mocks()
    existing_short = MagicMock()
    service._repository.get_by_video_and_type = AsyncMock(return_value=existing_short)

    results = await service.summarize(
        _fake_video(), _fake_transcript(), summary_types=[SummaryType.SHORT]
    )

    assert results == [existing_short]
    service._repository.list_by_video.assert_not_called()
    service._content_prep.get_combined_summary.assert_not_called()
    service._content_prep.get_combined_summary_with_chunks.assert_not_called()


async def test_include_mindmap_generates_and_persists_when_missing():
    service = _service_with_mocks()
    existing_short = MagicMock()
    existing_short.id = uuid.uuid4()
    existing_short.mindmap_markdown = None
    existing_short.key_takeaways = {}
    existing_short.topics = {}
    existing_short.timestamped_sections = []

    service._repository.get_by_video_and_type = AsyncMock(return_value=existing_short)
    service._repository.list_by_video = AsyncMock(return_value=[existing_short])
    service._repository.update_mindmap = AsyncMock()

    results = await service.summarize(
        _fake_video(),
        _fake_transcript(),
        summary_types=[SummaryType.SHORT],
        include_mindmap=True,
    )

    assert results == [existing_short]
    service._content_prep.get_combined_summary.assert_called_once()
    service._repository.update_mindmap.assert_called_once_with(existing_short.id, "mock generated text")
    assert existing_short.mindmap_markdown == "mock generated text"

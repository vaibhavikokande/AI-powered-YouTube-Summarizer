import uuid
from unittest.mock import AsyncMock, MagicMock

from app.services.content_prep_service import ContentPrepService


def _fake_transcript(cached_text: str | None = None):
    transcript = MagicMock()
    transcript.id = uuid.uuid4()
    transcript.chunk_summaries_text = cached_text
    transcript.segments = [{"start": 0.0, "duration": 2.0, "text": "hello world"}]
    return transcript


def _service_with_mocks() -> ContentPrepService:
    llm = MagicMock()
    llm.generate_text = AsyncMock(return_value="chunk summary")

    service = ContentPrepService(session=MagicMock(), llm_provider=llm)
    service._repository = MagicMock()
    service._repository.update_chunk_summaries = AsyncMock()
    return service


async def test_get_combined_summary_returns_cached_text_without_llm_call():
    service = _service_with_mocks()
    transcript = _fake_transcript(cached_text="already computed")

    result = await service.get_combined_summary(transcript)

    assert result == "already computed"
    service._llm.generate_text.assert_not_called()
    service._repository.update_chunk_summaries.assert_not_called()


async def test_get_combined_summary_computes_and_caches_when_missing():
    service = _service_with_mocks()
    transcript = _fake_transcript(cached_text=None)

    result = await service.get_combined_summary(transcript)

    assert result == "chunk summary"
    service._llm.generate_text.assert_called_once()
    service._repository.update_chunk_summaries.assert_called_once_with(transcript.id, "chunk summary")


async def test_get_combined_summary_with_chunks_returns_chunks_and_summaries():
    service = _service_with_mocks()
    transcript = _fake_transcript(cached_text=None)

    combined, chunks, chunk_summaries = await service.get_combined_summary_with_chunks(transcript)

    assert combined == "chunk summary"
    assert len(chunks) == 1
    assert chunk_summaries == ["chunk summary"]

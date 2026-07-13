import uuid
from unittest.mock import AsyncMock, MagicMock, patch

from app.services.transcript_service import TranscriptService
from app.services.youtube_transcript_fetcher import FetchedTranscript
from app.schemas.transcript import TranscriptSegment


def _service_with_mocks():
    service = TranscriptService(session=MagicMock())
    service._repository = MagicMock()
    service._repository.get_by_video_id = AsyncMock(return_value=None)
    service._repository.create = AsyncMock(return_value="persisted-transcript")
    return service


async def test_returns_existing_transcript_without_fetching():
    service = _service_with_mocks()
    service._repository.get_by_video_id = AsyncMock(return_value="existing-transcript")

    with patch.object(service._fetcher.__class__, "fetch") as mock_fetch:
        result = await service.get_or_fetch_transcript(uuid.uuid4(), "dQw4w9WgXcQ")

    assert result == "existing-transcript"
    mock_fetch.assert_not_called()


async def test_fetches_and_persists_when_no_transcript_exists():
    service = _service_with_mocks()

    fetched = FetchedTranscript(
        language="en",
        source_language=None,
        is_auto_generated=False,
        is_translated=False,
        full_text="hello world",
        segments=[TranscriptSegment(start=0.0, duration=1.0, text="hello world")],
    )

    with patch.object(service._fetcher.__class__, "fetch", return_value=fetched):
        result = await service.get_or_fetch_transcript(uuid.uuid4(), "dQw4w9WgXcQ")

    assert result == "persisted-transcript"
    service._repository.create.assert_called_once()
    _, kwargs = service._repository.create.call_args
    assert kwargs["language"] == "en"
    assert kwargs["full_text"] == "hello world"

import uuid
from datetime import datetime, timezone
from unittest.mock import AsyncMock, patch

from fastapi.testclient import TestClient

from app.db.session import get_db
from app.main import app
from app.models.enums import SummaryType
from app.schemas.summary import KeyTakeaways, SummaryResponse, Topics


async def _override_get_db():
    yield None


app.dependency_overrides[get_db] = _override_get_db
client = TestClient(app)


def _fake_video():
    video = AsyncMock()
    video.id = uuid.uuid4()
    video.title = "Test Video"
    video.youtube_video_id = "dQw4w9WgXcQ"
    return video


def _fake_transcript():
    transcript = AsyncMock()
    transcript.id = uuid.uuid4()
    transcript.segments = [{"start": 0.0, "duration": 2.0, "text": "hello world"}]
    return transcript


def _fake_summary_response() -> SummaryResponse:
    return SummaryResponse(
        id=uuid.uuid4(),
        video_id=uuid.uuid4(),
        summary_type=SummaryType.MEDIUM,
        content="A medium summary.",
        key_takeaways=KeyTakeaways(),
        timestamped_sections=[],
        topics=Topics(),
        mindmap_markdown=None,
        llm_provider="claude",
        created_at=datetime.now(timezone.utc),
    )


def test_summarize_returns_requested_summaries():
    with (
        patch("app.api.v1.endpoints.summarize.VideoService") as MockVideoService,
        patch("app.api.v1.endpoints.summarize.TranscriptService") as MockTranscriptService,
        patch("app.api.v1.endpoints.summarize.SummarizationService") as MockSummarizationService,
    ):
        MockVideoService.return_value.get_or_fetch_video = AsyncMock(return_value=_fake_video())
        MockTranscriptService.return_value.get_or_fetch_transcript = AsyncMock(
            return_value=_fake_transcript()
        )
        MockSummarizationService.return_value.summarize = AsyncMock(
            return_value=[_fake_summary_response()]
        )

        response = client.post(
            "/api/v1/summarize",
            json={"url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ", "summary_types": ["medium"]},
        )

    assert response.status_code == 200
    body = response.json()
    assert len(body) == 1
    assert body[0]["summary_type"] == "medium"
    assert body[0]["content"] == "A medium summary."


def test_summarize_missing_url_returns_422():
    response = client.post("/api/v1/summarize", json={})
    assert response.status_code == 422

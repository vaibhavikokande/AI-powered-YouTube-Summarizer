import uuid
from unittest.mock import AsyncMock, patch

from fastapi.testclient import TestClient

from app.db.session import get_db
from app.main import app
from app.schemas.transcript import TranscriptResponse


async def _override_get_db():
    yield None


app.dependency_overrides[get_db] = _override_get_db
client = TestClient(app)


def _fake_video():
    video = AsyncMock()
    video.id = uuid.uuid4()
    video.youtube_video_id = "dQw4w9WgXcQ"
    return video


def _fake_transcript_response() -> TranscriptResponse:
    return TranscriptResponse(
        id=uuid.uuid4(),
        video_id=uuid.uuid4(),
        language="en",
        is_auto_generated=False,
        is_translated=False,
        source_language=None,
        full_text="hello world",
        segments=[{"start": 0.0, "duration": 1.0, "text": "hello world"}],
    )


def test_get_transcript_returns_transcript_data():
    with (
        patch("app.api.v1.endpoints.transcript.VideoService") as MockVideoService,
        patch("app.api.v1.endpoints.transcript.TranscriptService") as MockTranscriptService,
    ):
        MockVideoService.return_value.get_or_fetch_video = AsyncMock(return_value=_fake_video())
        MockTranscriptService.return_value.get_or_fetch_transcript = AsyncMock(
            return_value=_fake_transcript_response()
        )

        response = client.get(
            "/api/v1/transcript", params={"url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ"}
        )

    assert response.status_code == 200
    body = response.json()
    assert body["language"] == "en"
    assert body["full_text"] == "hello world"


def test_get_transcript_missing_url_param_returns_422():
    response = client.get("/api/v1/transcript")
    assert response.status_code == 422

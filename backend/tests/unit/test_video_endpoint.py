import uuid
from datetime import datetime, timezone
from unittest.mock import AsyncMock, patch

from fastapi.testclient import TestClient

from app.db.session import get_db
from app.main import app
from app.schemas.video import VideoResponse


async def _override_get_db():
    # VideoService is mocked in every test below, so no real session is needed.
    yield None


app.dependency_overrides[get_db] = _override_get_db
client = TestClient(app)


def _fake_video_response() -> VideoResponse:
    return VideoResponse(
        id=uuid.uuid4(),
        youtube_video_id="dQw4w9WgXcQ",
        url="https://www.youtube.com/watch?v=dQw4w9WgXcQ",
        title="Sample Video",
        description=None,
        channel_name="Sample Channel",
        channel_id="UC123",
        thumbnail_url="https://img.example.com/thumb.jpg",
        duration_seconds=3600,
        view_count=1000,
        upload_date="2024-01-15",
        original_language="en",
        created_at=datetime.now(timezone.utc),
    )


def test_get_video_returns_metadata():
    with patch("app.api.v1.endpoints.video.VideoService") as MockService:
        MockService.return_value.get_or_fetch_video = AsyncMock(
            return_value=_fake_video_response()
        )

        response = client.get(
            "/api/v1/video", params={"url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ"}
        )

    assert response.status_code == 200
    body = response.json()
    assert body["youtube_video_id"] == "dQw4w9WgXcQ"
    assert body["title"] == "Sample Video"


def test_get_video_missing_url_param_returns_422():
    response = client.get("/api/v1/video")
    assert response.status_code == 422

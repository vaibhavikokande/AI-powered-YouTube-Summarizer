import uuid
from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock, patch

from fastapi.testclient import TestClient

from app.db.session import get_db
from app.main import app
from app.schemas.video import VideoResponse


async def _override_get_db():
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


def _fake_video_orm_object() -> MagicMock:
    response = _fake_video_response()
    video = MagicMock()
    for field, value in response.model_dump().items():
        setattr(video, field, value)
    return video


def test_get_video_returns_metadata_on_cache_miss_and_populates_cache():
    with (
        patch("app.api.v1.endpoints.video.cache_get_json", new=AsyncMock(return_value=None)),
        patch("app.api.v1.endpoints.video.cache_set_json", new=AsyncMock()) as mock_cache_set,
        patch("app.api.v1.endpoints.video.VideoService") as MockService,
    ):
        MockService.return_value.get_or_fetch_video = AsyncMock(
            return_value=_fake_video_orm_object()
        )

        response = client.get(
            "/api/v1/video", params={"url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ"}
        )

    assert response.status_code == 200
    body = response.json()
    assert body["youtube_video_id"] == "dQw4w9WgXcQ"
    assert body["title"] == "Sample Video"
    mock_cache_set.assert_called_once()


def test_get_video_returns_metadata_on_cache_hit_without_calling_service():
    cached_payload = _fake_video_response().model_dump(mode="json")

    with (
        patch("app.api.v1.endpoints.video.cache_get_json", new=AsyncMock(return_value=cached_payload)),
        patch("app.api.v1.endpoints.video.VideoService") as MockService,
    ):
        response = client.get(
            "/api/v1/video", params={"url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ"}
        )

    assert response.status_code == 200
    assert response.json()["title"] == "Sample Video"
    MockService.return_value.get_or_fetch_video.assert_not_called()


def test_get_video_missing_url_param_returns_422():
    response = client.get("/api/v1/video")
    assert response.status_code == 422

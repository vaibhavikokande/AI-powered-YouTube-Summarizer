import uuid
from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock, patch

from fastapi.testclient import TestClient

from app.api.deps import get_current_user
from app.db.session import get_db
from app.main import app
from app.schemas.video import VideoResponse


async def _override_get_db():
    yield None


def _fake_current_user():
    user = MagicMock()
    user.id = uuid.uuid4()
    return user


app.dependency_overrides[get_db] = _override_get_db
app.dependency_overrides[get_current_user] = _fake_current_user
client = TestClient(app)


def _fake_video_response() -> VideoResponse:
    return VideoResponse(
        id=uuid.uuid4(),
        youtube_video_id="dQw4w9WgXcQ",
        url="https://www.youtube.com/watch?v=dQw4w9WgXcQ",
        title="Test Video",
        description=None,
        channel_name=None,
        channel_id=None,
        thumbnail_url=None,
        duration_seconds=None,
        view_count=None,
        upload_date=None,
        original_language=None,
        created_at=datetime.now(timezone.utc),
    )


def test_get_history_returns_paginated_videos():
    with patch("app.api.v1.endpoints.history.HistoryService") as MockHistoryService:
        MockHistoryService.return_value.list_history = AsyncMock(
            return_value=([_fake_video_response()], 1)
        )

        response = client.get("/api/v1/history")

    assert response.status_code == 200
    body = response.json()
    assert body["total"] == 1
    assert len(body["items"]) == 1


def test_get_history_passes_search_and_pagination_through():
    with patch("app.api.v1.endpoints.history.HistoryService") as MockHistoryService:
        MockHistoryService.return_value.list_history = AsyncMock(return_value=([], 0))

        response = client.get("/api/v1/history", params={"search": "python", "limit": 5, "offset": 10})

    assert response.status_code == 200
    _, kwargs = MockHistoryService.return_value.list_history.call_args
    assert kwargs["search"] == "python"
    assert kwargs["limit"] == 5
    assert kwargs["offset"] == 10

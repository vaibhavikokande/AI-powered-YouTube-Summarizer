import uuid
from datetime import datetime, timezone
from unittest.mock import AsyncMock, patch

from fastapi.testclient import TestClient

from app.db.session import get_db
from app.main import app
from app.schemas.note import NoteResponse


async def _override_get_db():
    yield None


app.dependency_overrides[get_db] = _override_get_db
client = TestClient(app)


def test_generate_notes_returns_note():
    with (
        patch("app.api.v1.endpoints.notes.VideoService") as MockVideoService,
        patch("app.api.v1.endpoints.notes.TranscriptService") as MockTranscriptService,
        patch("app.api.v1.endpoints.notes.NotesService") as MockNotesService,
    ):
        MockVideoService.return_value.get_or_fetch_video = AsyncMock(return_value=AsyncMock())
        MockTranscriptService.return_value.get_or_fetch_transcript = AsyncMock(
            return_value=AsyncMock()
        )
        MockNotesService.return_value.generate = AsyncMock(
            return_value=NoteResponse(
                id=uuid.uuid4(),
                video_id=uuid.uuid4(),
                content_markdown="## Notes\n- Point one",
                created_at=datetime.now(timezone.utc),
            )
        )

        response = client.post(
            "/api/v1/notes", json={"url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ"}
        )

    assert response.status_code == 200
    body = response.json()
    assert body["content_markdown"] == "## Notes\n- Point one"


def test_generate_notes_missing_url_returns_422():
    response = client.post("/api/v1/notes", json={})
    assert response.status_code == 422

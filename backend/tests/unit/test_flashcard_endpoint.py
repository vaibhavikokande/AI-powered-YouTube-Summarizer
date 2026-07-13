import uuid
from unittest.mock import AsyncMock, patch

from fastapi.testclient import TestClient

from app.db.session import get_db
from app.main import app
from app.schemas.flashcard import FlashcardResponse


async def _override_get_db():
    yield None


app.dependency_overrides[get_db] = _override_get_db
client = TestClient(app)


def test_generate_flashcards_returns_items():
    with (
        patch("app.api.v1.endpoints.flashcards.VideoService") as MockVideoService,
        patch("app.api.v1.endpoints.flashcards.TranscriptService") as MockTranscriptService,
        patch("app.api.v1.endpoints.flashcards.FlashcardService") as MockFlashcardService,
    ):
        MockVideoService.return_value.get_or_fetch_video = AsyncMock(return_value=AsyncMock())
        MockTranscriptService.return_value.get_or_fetch_transcript = AsyncMock(
            return_value=AsyncMock()
        )
        MockFlashcardService.return_value.generate = AsyncMock(
            return_value=[FlashcardResponse(id=uuid.uuid4(), question="Q1?", answer="A1.")]
        )

        response = client.post(
            "/api/v1/flashcards", json={"url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ"}
        )

    assert response.status_code == 200
    body = response.json()
    assert len(body) == 1
    assert body[0]["question"] == "Q1?"


def test_generate_flashcards_missing_url_returns_422():
    response = client.post("/api/v1/flashcards", json={})
    assert response.status_code == 422

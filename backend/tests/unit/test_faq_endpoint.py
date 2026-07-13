import uuid
from datetime import datetime, timezone
from unittest.mock import AsyncMock, patch

from fastapi.testclient import TestClient

from app.db.session import get_db
from app.main import app
from app.schemas.faq import FAQItemResponse


async def _override_get_db():
    yield None


app.dependency_overrides[get_db] = _override_get_db
client = TestClient(app)


def test_generate_faq_returns_items():
    with (
        patch("app.api.v1.endpoints.faq.VideoService") as MockVideoService,
        patch("app.api.v1.endpoints.faq.TranscriptService") as MockTranscriptService,
        patch("app.api.v1.endpoints.faq.FAQService") as MockFAQService,
    ):
        MockVideoService.return_value.get_or_fetch_video = AsyncMock(return_value=AsyncMock())
        MockTranscriptService.return_value.get_or_fetch_transcript = AsyncMock(
            return_value=AsyncMock()
        )
        MockFAQService.return_value.generate = AsyncMock(
            return_value=[
                FAQItemResponse(
                    id=uuid.uuid4(),
                    question="What is X?",
                    answer="X is Y.",
                    created_at=datetime.now(timezone.utc),
                )
            ]
        )

        response = client.post(
            "/api/v1/faq", json={"url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ"}
        )

    assert response.status_code == 200
    body = response.json()
    assert len(body) == 1
    assert body[0]["question"] == "What is X?"


def test_generate_faq_missing_url_returns_422():
    response = client.post("/api/v1/faq", json={})
    assert response.status_code == 422

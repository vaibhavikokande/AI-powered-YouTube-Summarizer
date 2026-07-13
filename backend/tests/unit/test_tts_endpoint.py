import uuid
from unittest.mock import AsyncMock, MagicMock, patch

from fastapi.testclient import TestClient

from app.db.session import get_db
from app.main import app


async def _override_get_db():
    yield None


app.dependency_overrides[get_db] = _override_get_db
client = TestClient(app)


def test_get_voice_summary_returns_audio():
    fake_summary = MagicMock()
    fake_summary.content = "This is the summary text."

    with (
        patch("app.api.v1.endpoints.tts.SummaryRepository") as MockRepo,
        patch("app.api.v1.endpoints.tts.TTSService") as MockTTS,
    ):
        MockRepo.return_value.get_by_id = AsyncMock(return_value=fake_summary)
        MockTTS.return_value.generate_audio = AsyncMock(return_value=b"fake-audio-bytes")

        response = client.get("/api/v1/tts", params={"summary_id": str(uuid.uuid4())})

    assert response.status_code == 200
    assert response.content == b"fake-audio-bytes"
    assert response.headers["content-type"] == "audio/mpeg"


def test_get_voice_summary_returns_404_when_not_found():
    with patch("app.api.v1.endpoints.tts.SummaryRepository") as MockRepo:
        MockRepo.return_value.get_by_id = AsyncMock(return_value=None)

        response = client.get("/api/v1/tts", params={"summary_id": str(uuid.uuid4())})

    assert response.status_code == 404

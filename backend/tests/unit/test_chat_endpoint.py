import uuid
from unittest.mock import AsyncMock, MagicMock, patch

from fastapi.testclient import TestClient

from app.db.session import get_db
from app.main import app


async def _override_get_db():
    yield None


app.dependency_overrides[get_db] = _override_get_db
client = TestClient(app)


async def _fake_ask(video, transcript, chat_session, question):
    for token in ["Hel", "lo"]:
        yield token


def test_chat_streams_tokens_then_final_session_event():
    fake_video = MagicMock()
    fake_video.id = uuid.uuid4()
    fake_video.youtube_video_id = "dQw4w9WgXcQ"

    fake_session = MagicMock()
    fake_session.id = uuid.uuid4()

    with (
        patch("app.api.v1.endpoints.chat.VideoService") as MockVideoService,
        patch("app.api.v1.endpoints.chat.TranscriptService") as MockTranscriptService,
        patch("app.api.v1.endpoints.chat.ChatService") as MockChatService,
    ):
        MockVideoService.return_value.get_or_fetch_video = AsyncMock(return_value=fake_video)
        MockTranscriptService.return_value.get_or_fetch_transcript = AsyncMock(
            return_value=MagicMock()
        )
        MockChatService.return_value.get_or_create_session = AsyncMock(return_value=fake_session)
        MockChatService.return_value.ask = _fake_ask

        response = client.post(
            "/api/v1/chat",
            json={"url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ", "message": "What is X?"},
        )

    assert response.status_code == 200
    body = response.text
    assert 'data: {"token": "Hel"}' in body
    assert 'data: {"token": "lo"}' in body
    assert f'"session_id": "{fake_session.id}"' in body
    assert '"done": true' in body


def test_chat_missing_message_returns_422():
    response = client.post(
        "/api/v1/chat", json={"url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ"}
    )
    assert response.status_code == 422

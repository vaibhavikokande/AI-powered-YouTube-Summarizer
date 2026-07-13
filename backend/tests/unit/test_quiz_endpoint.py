import uuid
from unittest.mock import AsyncMock, patch

from fastapi.testclient import TestClient

from app.db.session import get_db
from app.main import app
from app.schemas.quiz import QuizQuestionResponse, QuizResponse


async def _override_get_db():
    yield None


app.dependency_overrides[get_db] = _override_get_db
client = TestClient(app)


def test_generate_quiz_returns_quiz():
    with (
        patch("app.api.v1.endpoints.quiz.VideoService") as MockVideoService,
        patch("app.api.v1.endpoints.quiz.TranscriptService") as MockTranscriptService,
        patch("app.api.v1.endpoints.quiz.QuizService") as MockQuizService,
    ):
        MockVideoService.return_value.get_or_fetch_video = AsyncMock(return_value=AsyncMock())
        MockTranscriptService.return_value.get_or_fetch_transcript = AsyncMock(
            return_value=AsyncMock()
        )
        MockQuizService.return_value.generate = AsyncMock(
            return_value=QuizResponse(
                id=uuid.uuid4(),
                title="Test Quiz",
                questions=[
                    QuizQuestionResponse(
                        id=uuid.uuid4(),
                        question_type="mcq",
                        question_text="What is X?",
                        options=["A", "B"],
                        correct_answer="A",
                        explanation=None,
                    )
                ],
            )
        )

        response = client.post(
            "/api/v1/quiz", json={"url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ"}
        )

    assert response.status_code == 200
    body = response.json()
    assert body["title"] == "Test Quiz"
    assert len(body["questions"]) == 1


def test_generate_quiz_missing_url_returns_422():
    response = client.post("/api/v1/quiz", json={})
    assert response.status_code == 422

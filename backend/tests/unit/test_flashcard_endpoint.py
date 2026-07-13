from unittest.mock import MagicMock, patch

from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_generate_flashcards_enqueues_job_and_returns_task_id():
    with patch("app.api.v1.endpoints.flashcards.generate_flashcards_task") as mock_task:
        mock_task.delay.return_value = MagicMock(id="task-abc")

        response = client.post(
            "/api/v1/flashcards", json={"url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ"}
        )

    assert response.status_code == 200
    body = response.json()
    assert body["task_id"] == "task-abc"
    mock_task.delay.assert_called_once()


def test_generate_flashcards_missing_url_returns_422():
    response = client.post("/api/v1/flashcards", json={})
    assert response.status_code == 422

from unittest.mock import MagicMock, patch

from fastapi.testclient import TestClient

from app.db.session import get_db
from app.main import app


async def _override_get_db():
    yield None


app.dependency_overrides[get_db] = _override_get_db
client = TestClient(app)


def test_generate_notes_enqueues_job_and_returns_task_id():
    with patch("app.api.v1.endpoints.notes.generate_notes_task") as mock_task:
        mock_task.delay.return_value = MagicMock(id="task-456")

        response = client.post(
            "/api/v1/notes", json={"url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ"}
        )

    assert response.status_code == 200
    body = response.json()
    assert body["task_id"] == "task-456"
    mock_task.delay.assert_called_once_with(
        "https://www.youtube.com/watch?v=dQw4w9WgXcQ", None
    )


def test_generate_notes_missing_url_returns_422():
    response = client.post("/api/v1/notes", json={})
    assert response.status_code == 422

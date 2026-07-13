from unittest.mock import MagicMock, patch

from fastapi.testclient import TestClient

from app.db.session import get_db
from app.main import app


async def _override_get_db():
    # get_current_user_optional still declares a `db` dependency even when
    # no Authorization header is sent (FastAPI resolves all declared
    # dependencies before the endpoint body runs) — override it so tests
    # don't try to open a real DB connection.
    yield None


app.dependency_overrides[get_db] = _override_get_db
client = TestClient(app)


def test_summarize_enqueues_job_and_returns_task_id():
    with patch("app.api.v1.endpoints.summarize.summarize_video_task") as mock_task:
        mock_task.delay.return_value = MagicMock(id="task-123")

        response = client.post(
            "/api/v1/summarize",
            json={"url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ", "summary_types": ["medium"]},
        )

    assert response.status_code == 200
    body = response.json()
    assert body["task_id"] == "task-123"
    assert body["status"] == "queued"
    mock_task.delay.assert_called_once_with(
        "https://www.youtube.com/watch?v=dQw4w9WgXcQ", ["medium"], "en", False, None
    )


def test_summarize_rejects_invalid_url_before_enqueuing():
    with patch("app.api.v1.endpoints.summarize.summarize_video_task") as mock_task:
        response = client.post("/api/v1/summarize", json={"url": "https://vimeo.com/12345"})

    assert response.status_code != 200
    mock_task.delay.assert_not_called()


def test_summarize_missing_url_returns_422():
    response = client.post("/api/v1/summarize", json={})
    assert response.status_code == 422

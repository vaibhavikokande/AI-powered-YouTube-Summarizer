from unittest.mock import MagicMock, patch

from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_get_job_status_pending():
    with patch("app.api.v1.endpoints.jobs.AsyncResult") as MockAsyncResult:
        mock_result = MagicMock()
        mock_result.status = "PENDING"
        mock_result.successful.return_value = False
        mock_result.failed.return_value = False
        MockAsyncResult.return_value = mock_result

        response = client.get("/api/v1/jobs/some-task-id")

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "PENDING"
    assert body["result"] is None


def test_get_job_status_success_includes_result():
    with patch("app.api.v1.endpoints.jobs.AsyncResult") as MockAsyncResult:
        mock_result = MagicMock()
        mock_result.status = "SUCCESS"
        mock_result.successful.return_value = True
        mock_result.failed.return_value = False
        mock_result.result = [{"content": "done"}]
        MockAsyncResult.return_value = mock_result

        response = client.get("/api/v1/jobs/some-task-id")

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "SUCCESS"
    assert body["result"] == [{"content": "done"}]


def test_get_job_status_failure_includes_error():
    with patch("app.api.v1.endpoints.jobs.AsyncResult") as MockAsyncResult:
        mock_result = MagicMock()
        mock_result.status = "FAILURE"
        mock_result.successful.return_value = False
        mock_result.failed.return_value = True
        mock_result.result = ValueError("boom")
        MockAsyncResult.return_value = mock_result

        response = client.get("/api/v1/jobs/some-task-id")

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "FAILURE"
    assert "boom" in body["error"]

import uuid
from unittest.mock import AsyncMock, MagicMock, patch

from fastapi.testclient import TestClient

from app.db.session import get_db
from app.main import app
from app.services.export_service import ExportedFile


async def _override_get_db():
    yield None


app.dependency_overrides[get_db] = _override_get_db
client = TestClient(app)


def test_download_returns_file_with_correct_headers():
    fake_summary = MagicMock()
    fake_summary.video_id = uuid.uuid4()
    fake_video = MagicMock()
    fake_video.title = "My Video"

    with (
        patch("app.api.v1.endpoints.download.SummaryRepository") as MockSummaryRepo,
        patch("app.api.v1.endpoints.download.VideoRepository") as MockVideoRepo,
        patch("app.api.v1.endpoints.download.ExportService") as MockExportService,
    ):
        MockSummaryRepo.return_value.get_by_id = AsyncMock(return_value=fake_summary)
        MockVideoRepo.return_value.get_by_id = AsyncMock(return_value=fake_video)
        MockExportService.return_value.export.return_value = ExportedFile(
            content=b"file-bytes", media_type="text/plain", filename="My_Video.txt"
        )

        response = client.get(
            "/api/v1/download", params={"summary_id": str(uuid.uuid4()), "format": "txt"}
        )

    assert response.status_code == 200
    assert response.content == b"file-bytes"
    assert "My_Video.txt" in response.headers["content-disposition"]


def test_download_returns_404_when_summary_not_found():
    with patch("app.api.v1.endpoints.download.SummaryRepository") as MockSummaryRepo:
        MockSummaryRepo.return_value.get_by_id = AsyncMock(return_value=None)

        response = client.get(
            "/api/v1/download", params={"summary_id": str(uuid.uuid4()), "format": "txt"}
        )

    assert response.status_code == 404


def test_download_rejects_invalid_format():
    response = client.get(
        "/api/v1/download", params={"summary_id": str(uuid.uuid4()), "format": "epub"}
    )
    assert response.status_code == 422

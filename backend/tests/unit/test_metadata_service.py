from unittest.mock import patch

import pytest
import yt_dlp

from app.core.exceptions import ExternalServiceError, ValidationAppError
from app.services.metadata_service import MetadataService

FAKE_INFO = {
    "title": "Sample Video",
    "description": "A description",
    "uploader": "Sample Channel",
    "channel_id": "UC123",
    "thumbnail": "https://img.example.com/thumb.jpg",
    "duration": 3600,
    "view_count": 1000,
    "upload_date": "20240115",
    "language": "en",
}


async def test_fetch_metadata_maps_yt_dlp_fields():
    service = MetadataService()

    with patch.object(MetadataService, "_extract_info", return_value=FAKE_INFO):
        metadata = await service.fetch_metadata("https://www.youtube.com/watch?v=dQw4w9WgXcQ")

    assert metadata.youtube_video_id == "dQw4w9WgXcQ"
    assert metadata.title == "Sample Video"
    assert metadata.channel_name == "Sample Channel"
    assert metadata.upload_date == "2024-01-15"
    assert metadata.duration_seconds == 3600


async def test_fetch_metadata_wraps_download_errors():
    service = MetadataService()

    with patch.object(
        MetadataService,
        "_extract_info",
        side_effect=yt_dlp.utils.DownloadError("private video"),
    ):
        with pytest.raises(ExternalServiceError):
            await service.fetch_metadata("https://www.youtube.com/watch?v=dQw4w9WgXcQ")


async def test_fetch_metadata_rejects_invalid_url_before_calling_yt_dlp():
    service = MetadataService()

    with patch.object(MetadataService, "_extract_info") as mock_extract:
        with pytest.raises(ValidationAppError):
            await service.fetch_metadata("https://vimeo.com/12345")

    mock_extract.assert_not_called()

import asyncio
import logging
from typing import Any

import yt_dlp

from app.core.exceptions import ExternalServiceError
from app.schemas.video import VideoMetadata
from app.utils.youtube import canonical_watch_url, extract_video_id

logger = logging.getLogger(__name__)

_YDL_OPTS: dict[str, Any] = {
    "quiet": True,
    "no_warnings": True,
    "skip_download": True,
    "noplaylist": True,
}


class MetadataService:
    """Fetches video metadata straight from YouTube — no API key required.

    Uses yt-dlp's info extractor rather than the official Data API so the
    project works out of the box without a Google Cloud project/quota.
    """

    async def fetch_metadata(self, url: str) -> VideoMetadata:
        video_id = extract_video_id(url)
        watch_url = canonical_watch_url(video_id)

        try:
            info = await asyncio.to_thread(self._extract_info, watch_url)
        except yt_dlp.utils.DownloadError as exc:
            logger.warning("yt-dlp failed to fetch metadata for %s: %s", watch_url, exc)
            raise ExternalServiceError(
                "This video is unavailable, private, age-restricted, or region-restricted."
            ) from exc

        return VideoMetadata(
            youtube_video_id=video_id,
            url=watch_url,
            title=info.get("title"),
            description=info.get("description"),
            channel_name=info.get("uploader") or info.get("channel"),
            channel_id=info.get("channel_id"),
            thumbnail_url=info.get("thumbnail"),
            duration_seconds=int(info["duration"]) if info.get("duration") is not None else None,
            view_count=info.get("view_count"),
            upload_date=self._format_upload_date(info.get("upload_date")),
            original_language=info.get("language"),
        )

    @staticmethod
    def _extract_info(watch_url: str) -> dict[str, Any]:
        with yt_dlp.YoutubeDL(_YDL_OPTS) as ydl:
            return ydl.extract_info(watch_url, download=False)

    @staticmethod
    def _format_upload_date(raw: str | None) -> str | None:
        """yt-dlp returns dates as YYYYMMDD; normalize to ISO 8601."""
        if not raw or len(raw) != 8:
            return raw
        return f"{raw[0:4]}-{raw[4:6]}-{raw[6:8]}"

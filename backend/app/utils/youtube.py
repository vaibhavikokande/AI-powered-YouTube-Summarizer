import re
from urllib.parse import parse_qs, urlparse

from app.core.exceptions import ValidationAppError

_VIDEO_ID_PATTERN = re.compile(r"^[A-Za-z0-9_-]{11}$")

_ALLOWED_HOSTS = {
    "youtube.com",
    "www.youtube.com",
    "m.youtube.com",
    "music.youtube.com",
    "youtube-nocookie.com",
    "www.youtube-nocookie.com",
    "youtu.be",
    "www.youtu.be",
}

_PATH_PREFIXES_WITH_ID = {"shorts", "embed", "live"}


def extract_video_id(url: str) -> str:
    """Extract the 11-character video id from any common YouTube URL shape.

    Supports /watch?v=, youtu.be short links, and /shorts, /embed, /live
    paths, with or without extra query params (timestamps, playlist ids).
    Raises ValidationAppError for anything else, so callers can fail fast
    before spending a network call on an unparseable URL.
    """
    url = url.strip()
    if not url:
        raise ValidationAppError("URL must not be empty")

    if not re.match(r"^https?://", url):
        url = f"https://{url}"

    parsed = urlparse(url)
    host = parsed.netloc.lower()

    if host not in _ALLOWED_HOSTS:
        raise ValidationAppError(f"'{host or url}' is not a recognized YouTube domain")

    video_id: str | None = None

    if host.endswith("youtu.be"):
        video_id = parsed.path.lstrip("/").split("/")[0] or None
    elif parsed.path == "/watch":
        video_id = parse_qs(parsed.query).get("v", [None])[0]
    else:
        path_parts = [p for p in parsed.path.split("/") if p]
        if len(path_parts) >= 2 and path_parts[0] in _PATH_PREFIXES_WITH_ID:
            video_id = path_parts[1]

    if not video_id or not _VIDEO_ID_PATTERN.match(video_id):
        raise ValidationAppError("Could not extract a valid YouTube video id from the URL")

    return video_id


def canonical_watch_url(video_id: str) -> str:
    return f"https://www.youtube.com/watch?v={video_id}"

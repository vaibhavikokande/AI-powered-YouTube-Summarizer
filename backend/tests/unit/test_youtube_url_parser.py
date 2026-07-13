import pytest

from app.core.exceptions import ValidationAppError
from app.utils.youtube import canonical_watch_url, extract_video_id


@pytest.mark.parametrize(
    "url",
    [
        "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
        "https://youtube.com/watch?v=dQw4w9WgXcQ&t=30s",
        "https://youtu.be/dQw4w9WgXcQ",
        "https://youtu.be/dQw4w9WgXcQ?t=10",
        "youtu.be/dQw4w9WgXcQ",
        "https://www.youtube.com/shorts/dQw4w9WgXcQ",
        "https://m.youtube.com/watch?v=dQw4w9WgXcQ",
        "https://www.youtube.com/embed/dQw4w9WgXcQ",
        "https://www.youtube.com/live/dQw4w9WgXcQ",
    ],
)
def test_extract_video_id_supports_common_url_shapes(url):
    assert extract_video_id(url) == "dQw4w9WgXcQ"


@pytest.mark.parametrize(
    "url",
    [
        "",
        "   ",
        "https://vimeo.com/12345",
        "https://www.youtube.com/watch?v=short",
        "https://www.youtube.com/",
        "not a url at all",
    ],
)
def test_extract_video_id_rejects_invalid_input(url):
    with pytest.raises(ValidationAppError):
        extract_video_id(url)


def test_canonical_watch_url_format():
    assert canonical_watch_url("dQw4w9WgXcQ") == "https://www.youtube.com/watch?v=dQw4w9WgXcQ"

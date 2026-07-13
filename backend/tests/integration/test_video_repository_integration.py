import pytest
from sqlalchemy.exc import IntegrityError

from app.repositories.video_repository import VideoRepository
from app.schemas.video import VideoMetadata

pytestmark = pytest.mark.integration


def _metadata(youtube_video_id: str = "dQw4w9WgXcQ") -> VideoMetadata:
    return VideoMetadata(
        youtube_video_id=youtube_video_id,
        url=f"https://www.youtube.com/watch?v={youtube_video_id}",
        title="Test Video",
        channel_name="Test Channel",
        duration_seconds=120,
        view_count=100,
        upload_date="2024-01-15",
        original_language="en",
    )


async def test_create_and_get_by_youtube_id(db_session):
    repo = VideoRepository(db_session)

    created = await repo.create(_metadata())
    fetched = await repo.get_by_youtube_id("dQw4w9WgXcQ")

    assert fetched is not None
    assert fetched.id == created.id
    assert fetched.title == "Test Video"


async def test_get_by_youtube_id_returns_none_when_missing(db_session):
    result = await VideoRepository(db_session).get_by_youtube_id("does-not-exist")

    assert result is None


async def test_youtube_video_id_uniqueness_is_enforced_at_the_db_level(db_session):
    repo = VideoRepository(db_session)
    await repo.create(_metadata("uniqueTestVid1"))

    with pytest.raises(IntegrityError):
        await repo.create(_metadata("uniqueTestVid1"))

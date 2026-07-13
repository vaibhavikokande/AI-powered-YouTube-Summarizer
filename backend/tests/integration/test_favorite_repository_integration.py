import pytest
from sqlalchemy.exc import IntegrityError

from app.repositories.favorite_repository import FavoriteRepository
from app.repositories.user_repository import UserRepository
from app.repositories.video_repository import VideoRepository
from app.schemas.video import VideoMetadata

pytestmark = pytest.mark.integration


async def _setup_user_and_video(db_session, suffix: str):
    user = await UserRepository(db_session).create(
        f"fav-test-{suffix}@example.com", hashed_password="hashed"
    )
    video = await VideoRepository(db_session).create(
        VideoMetadata(
            youtube_video_id=f"favTestVideo{suffix}",
            url=f"https://www.youtube.com/watch?v=favTestVideo{suffix}",
            title="Fav Test Video",
        )
    )
    return user, video


async def test_add_favorite_persists_and_is_listed(db_session):
    user, video = await _setup_user_and_video(db_session, "1")
    repo = FavoriteRepository(db_session)

    await repo.add(user.id, video.id)
    favorites = await repo.list_by_user(user.id)

    assert len(favorites) == 1
    assert favorites[0].video_id == video.id


async def test_duplicate_favorite_violates_unique_constraint(db_session):
    user, video = await _setup_user_and_video(db_session, "2")
    repo = FavoriteRepository(db_session)
    await repo.add(user.id, video.id)

    with pytest.raises(IntegrityError):
        await repo.add(user.id, video.id)

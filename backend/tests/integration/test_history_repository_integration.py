import pytest

from app.repositories.history_repository import HistoryRepository
from app.repositories.user_repository import UserRepository
from app.repositories.video_repository import VideoRepository
from app.schemas.video import VideoMetadata

pytestmark = pytest.mark.integration


async def test_touch_upserts_instead_of_duplicating_on_repeat_view(db_session):
    user = await UserRepository(db_session).create(
        "history-test@example.com", hashed_password="hashed"
    )
    video = await VideoRepository(db_session).create(
        VideoMetadata(
            youtube_video_id="historyTestVideo1",
            url="https://www.youtube.com/watch?v=historyTestVideo1",
            title="History Test Video",
        )
    )
    repo = HistoryRepository(db_session)

    first = await repo.touch(user.id, video.id)
    second = await repo.touch(user.id, video.id)

    assert first.id == second.id  # same row, not duplicated

    videos, total = await repo.list_by_user(user.id)
    assert total == 1
    assert videos[0].id == video.id


async def test_list_by_user_filters_by_search_title(db_session):
    user = await UserRepository(db_session).create(
        "history-search@example.com", hashed_password="hashed"
    )
    repo = HistoryRepository(db_session)
    video_repo = VideoRepository(db_session)

    matching = await video_repo.create(
        VideoMetadata(
            youtube_video_id="searchMatchVid1",
            url="https://www.youtube.com/watch?v=searchMatchVid1",
            title="Learning Python Basics",
        )
    )
    non_matching = await video_repo.create(
        VideoMetadata(
            youtube_video_id="searchMatchVid2",
            url="https://www.youtube.com/watch?v=searchMatchVid2",
            title="Cooking Pasta",
        )
    )
    await repo.touch(user.id, matching.id)
    await repo.touch(user.id, non_matching.id)

    videos, total = await repo.list_by_user(user.id, search="python")

    assert total == 1
    assert videos[0].id == matching.id

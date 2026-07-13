from app.db.base import Base
from app.models import (  # noqa: F401 -- import triggers mapper registration
    Bookmark,
    ChatMessage,
    ChatSession,
    Favorite,
    Flashcard,
    Note,
    Quiz,
    QuizQuestion,
    ShareLink,
    Summary,
    Transcript,
    User,
    Video,
)

EXPECTED_TABLES = {
    "users",
    "videos",
    "transcripts",
    "summaries",
    "chat_sessions",
    "chat_messages",
    "flashcards",
    "quizzes",
    "quiz_questions",
    "notes",
    "share_links",
    "favorites",
    "bookmarks",
}


def test_all_models_register_with_base_metadata():
    assert EXPECTED_TABLES.issubset(set(Base.metadata.tables.keys()))


def test_video_favorite_unique_constraint_is_declared():
    favorites_table = Base.metadata.tables["favorites"]
    constraint_names = {c.name for c in favorites_table.constraints}
    assert "uq_favorites_user_video" in constraint_names

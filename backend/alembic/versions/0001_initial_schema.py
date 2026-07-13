"""initial schema

Revision ID: 0001
Revises:
Create Date: 2026-07-13 00:00:00.000000

"""

import uuid
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "users",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, default=uuid.uuid4),
        sa.Column("email", sa.String(255), nullable=False),
        sa.Column("hashed_password", sa.String(255), nullable=True),
        sa.Column("full_name", sa.String(255), nullable=True),
        sa.Column("avatar_url", sa.String(1024), nullable=True),
        sa.Column("google_id", sa.String(255), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("is_superuser", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_users_email", "users", ["email"], unique=True)
    op.create_index("ix_users_google_id", "users", ["google_id"], unique=True)

    op.create_table(
        "videos",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, default=uuid.uuid4),
        sa.Column("youtube_video_id", sa.String(20), nullable=False),
        sa.Column("url", sa.String(512), nullable=False),
        sa.Column("title", sa.String(512), nullable=True),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("channel_name", sa.String(255), nullable=True),
        sa.Column("channel_id", sa.String(64), nullable=True),
        sa.Column("thumbnail_url", sa.String(1024), nullable=True),
        sa.Column("duration_seconds", sa.Integer(), nullable=True),
        sa.Column("view_count", sa.Integer(), nullable=True),
        sa.Column("upload_date", sa.String(32), nullable=True),
        sa.Column("original_language", sa.String(16), nullable=True),
        sa.Column(
            "created_by_user_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_videos_youtube_video_id", "videos", ["youtube_video_id"], unique=True)
    op.create_index("ix_videos_created_by_user_id", "videos", ["created_by_user_id"])

    op.create_table(
        "transcripts",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, default=uuid.uuid4),
        sa.Column(
            "video_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("videos.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("language", sa.String(16), nullable=False),
        sa.Column("is_auto_generated", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("is_translated", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("source_language", sa.String(16), nullable=True),
        sa.Column("full_text", sa.Text(), nullable=False),
        sa.Column("segments", postgresql.JSONB(), nullable=False, server_default="[]"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_transcripts_video_id", "transcripts", ["video_id"])

    op.create_table(
        "summaries",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, default=uuid.uuid4),
        sa.Column(
            "video_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("videos.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "user_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("summary_type", sa.String(16), nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("key_takeaways", postgresql.JSONB(), nullable=False, server_default="{}"),
        sa.Column("timestamped_sections", postgresql.JSONB(), nullable=False, server_default="[]"),
        sa.Column("topics", postgresql.JSONB(), nullable=False, server_default="{}"),
        sa.Column("mindmap_markdown", sa.Text(), nullable=True),
        sa.Column("llm_provider", sa.String(32), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_summaries_video_id", "summaries", ["video_id"])
    op.create_index("ix_summaries_user_id", "summaries", ["user_id"])
    op.create_check_constraint(
        "ck_summaries_summary_type",
        "summaries",
        "summary_type IN ('short', 'medium', 'detailed', 'bullet')",
    )

    op.create_table(
        "chat_sessions",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, default=uuid.uuid4),
        sa.Column(
            "video_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("videos.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "user_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_chat_sessions_video_id", "chat_sessions", ["video_id"])
    op.create_index("ix_chat_sessions_user_id", "chat_sessions", ["user_id"])

    op.create_table(
        "chat_messages",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, default=uuid.uuid4),
        sa.Column(
            "session_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("chat_sessions.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("role", sa.String(16), nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_chat_messages_session_id", "chat_messages", ["session_id"])
    op.create_check_constraint(
        "ck_chat_messages_role", "chat_messages", "role IN ('user', 'assistant')"
    )

    op.create_table(
        "flashcards",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, default=uuid.uuid4),
        sa.Column(
            "video_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("videos.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("question", sa.Text(), nullable=False),
        sa.Column("answer", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_flashcards_video_id", "flashcards", ["video_id"])

    op.create_table(
        "quizzes",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, default=uuid.uuid4),
        sa.Column(
            "video_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("videos.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("title", sa.String(255), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_quizzes_video_id", "quizzes", ["video_id"])

    op.create_table(
        "quiz_questions",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, default=uuid.uuid4),
        sa.Column(
            "quiz_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("quizzes.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("question_type", sa.String(16), nullable=False),
        sa.Column("question_text", sa.Text(), nullable=False),
        sa.Column("options", postgresql.JSONB(), nullable=True),
        sa.Column("correct_answer", sa.Text(), nullable=False),
        sa.Column("explanation", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_quiz_questions_quiz_id", "quiz_questions", ["quiz_id"])
    op.create_check_constraint(
        "ck_quiz_questions_question_type",
        "quiz_questions",
        "question_type IN ('mcq', 'true_false', 'fill_blank')",
    )

    op.create_table(
        "notes",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, default=uuid.uuid4),
        sa.Column(
            "video_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("videos.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "user_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("content_markdown", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_notes_video_id", "notes", ["video_id"])
    op.create_index("ix_notes_user_id", "notes", ["user_id"])

    op.create_table(
        "share_links",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, default=uuid.uuid4),
        sa.Column("token", sa.String(64), nullable=False),
        sa.Column(
            "summary_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("summaries.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_share_links_token", "share_links", ["token"], unique=True)
    op.create_index("ix_share_links_summary_id", "share_links", ["summary_id"])

    op.create_table(
        "favorites",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, default=uuid.uuid4),
        sa.Column(
            "user_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "video_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("videos.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.UniqueConstraint("user_id", "video_id", name="uq_favorites_user_video"),
    )
    op.create_index("ix_favorites_user_id", "favorites", ["user_id"])
    op.create_index("ix_favorites_video_id", "favorites", ["video_id"])

    op.create_table(
        "bookmarks",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, default=uuid.uuid4),
        sa.Column(
            "user_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "video_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("videos.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("timestamp_seconds", sa.Integer(), nullable=False),
        sa.Column("note", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_bookmarks_user_id", "bookmarks", ["user_id"])
    op.create_index("ix_bookmarks_video_id", "bookmarks", ["video_id"])


def downgrade() -> None:
    op.drop_table("bookmarks")
    op.drop_table("favorites")
    op.drop_table("share_links")
    op.drop_table("notes")
    op.drop_table("quiz_questions")
    op.drop_table("quizzes")
    op.drop_table("flashcards")
    op.drop_table("chat_messages")
    op.drop_table("chat_sessions")
    op.drop_table("summaries")
    op.drop_table("transcripts")
    op.drop_table("videos")
    op.drop_table("users")

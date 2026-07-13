# Changelog

All notable changes to this project are documented here.
Format loosely follows [Keep a Changelog](https://keepachangelog.com/).

## [Unreleased]

### Added — Step 3: YouTube URL validation + metadata extraction
- `app/utils/youtube.py`: `extract_video_id()` supporting `/watch?v=`,
  `youtu.be/`, `/shorts/`, `/embed/`, and `/live/` URL shapes (with or
  without extra query params), raising `ValidationAppError` for anything
  else so invalid input fails before any network call.
- `app/services/metadata_service.py`: fetches title, thumbnail, duration,
  channel name, upload date, view count, and description via **yt-dlp**
  (no YouTube Data API key required), run off the event loop with
  `asyncio.to_thread` since yt-dlp is a blocking call. Wraps `DownloadError`
  (private/deleted/region-locked videos) as `ExternalServiceError`.
- `app/repositories/video_repository.py` + `app/services/video_service.py`:
  get-or-fetch-and-persist orchestration, deduplicating videos by
  `youtube_video_id`.
- `GET /api/v1/video?url=...` endpoint (`app/api/v1/endpoints/video.py`).
- Tests: pure-logic URL parsing cases (11 shapes/rejections), a mocked
  yt-dlp metadata-mapping test, and an API test with the DB dependency
  overridden (no real Postgres needed) per `docs/SPEC.md`'s testing rules.

### Added — Step 2: Database models, schemas, Alembic migrations
- SQLAlchemy 2.0 async models for all 13 tables: `User`, `Video`,
  `Transcript`, `Summary`, `ChatSession`, `ChatMessage`, `Flashcard`, `Quiz`,
  `QuizQuestion`, `Note`, `ShareLink`, `Favorite`, `Bookmark`
  (`backend/app/models/`).
- Shared `UUIDPKMixin`/`TimestampMixin` and a naming convention on `Base`
  (`backend/app/db/base.py`) so every constraint/index has a predictable,
  referenceable name.
- Async engine/session setup + `get_db` FastAPI dependency
  (`backend/app/db/session.py`).
- Pydantic v2 request/response schemas mirroring every model
  (`backend/app/schemas/`), including nested structured shapes for
  `KeyTakeaways`, `Topics`, and `TimestampedSection` used by the future
  summarization engine.
- Alembic wired for async SQLAlchemy (`backend/alembic/env.py`) plus a
  hand-written initial migration (`0001_initial_schema.py`) creating all
  tables, indexes, FKs (cascade/set-null per relationship), and check
  constraints for the three string-backed enums.
- `docs/ARCHITECTURE.md` §5 updated with the actual schema/ERD and the
  reasoning behind cascade rules and enum-as-checked-string storage.
- `backend/tests/unit/test_models.py` verifying every model registers on
  `Base.metadata` and the `favorites` unique constraint is present.

### Added — Step 1: Project scaffolding
- Clean-architecture backend skeleton (`backend/app/{core,api,models,schemas,services,repositories,agents,prompts,vector_store,middleware,utils,db}`).
- FastAPI app factory (`backend/app/main.py`) with CORS, centralized `AppError`
  exception handling, and a `/api/v1/health` endpoint.
- Pydantic Settings-based config (`backend/app/core/config.py`) supporting a
  configurable `LLM_PROVIDER` (claude/openai/gemini) and `VECTOR_STORE_PROVIDER`
  (chroma/pinecone).
- Frontend skeleton: Vite + React + TypeScript + Tailwind, React Query wired
  up, dark mode toggle, axios client with JWT interceptor stub.
- `docker-compose.yml` wiring Postgres, Redis, ChromaDB, backend, Celery
  worker (placeholder), and the Vite dev server.
- `docs/ARCHITECTURE.md` and `docs/SPEC.md` establishing folder rules, naming
  conventions, prompt engineering guidelines, API standards, and testing
  strategy up front.
- `backend/tests/unit/test_health.py` as the first passing test.

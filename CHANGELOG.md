# Changelog

All notable changes to this project are documented here.
Format loosely follows [Keep a Changelog](https://keepachangelog.com/).

## [Unreleased]

### Added — Step 6: Summarization engine
- `app/utils/chunking.py`: splits transcript segments into chunks capped at
  a character budget (model-agnostic proxy for context-window limits),
  never splitting a segment and preserving accurate start/end timestamps
  per chunk — this is what makes multi-hour transcripts tractable.
- `app/prompts/summary_prompts.py`: named prompt functions for the map step
  (per-chunk summary), the reduce step (per summary-type instructions for
  short/medium/detailed/bullet), key takeaways extraction, topic/tag
  extraction, and timestamped section grouping — all instructed to only
  use information present in the source, never invent content.
- `app/services/summarization_service.py`: map-reduce orchestration.
  Chunks are summarized once (map) and reused across however many summary
  types are requested; key takeaways/topics/timestamped sections are
  likewise extracted once per video, not once per summary type. Already-
  generated summary types are skipped entirely (no LLM call) — mirrors the
  get-or-fetch pattern from `VideoService`/`TranscriptService`.
- `POST /api/v1/summarize` (`app/api/v1/endpoints/summarize.py`) — body:
  `{url, summary_types, language}` — resolves video → transcript →
  summaries in one request. Still synchronous today, same as `/video` and
  `/transcript`; Step 11 moves this behind a Celery job.
- `mindmap_markdown` stays `null` for now — mind map generation is Step 8's
  job (it updates the same `Summary` row rather than duplicating data).
- Tests: 5 pure-logic chunking cases, 2 service tests (missing-types
  generates + persists correctly with the right call counts; all-types-
  exist skips the LLM entirely), and an API test with dependencies mocked.

### Added — Step 5: LLM provider abstraction layer
- `app/agents/llm_provider.py`: `build_chat_model()` constructs the
  LangChain chat model (`ChatAnthropic`/`ChatOpenAI`/`ChatGoogleGenerativeAI`)
  selected by `LLM_PROVIDER`, raising a clean `ExternalServiceError` if that
  provider's API key isn't configured — instead of a confusing SDK-level
  auth error surfacing later.
- `LLMProvider` facade with `generate_text()` (plain completion) and
  `generate_structured()` (binds a Pydantic schema via LangChain's
  `with_structured_output`, so JSON mode / structured outputs work
  identically across all three providers — callers never hand-parse JSON).
- Transient failures (rate limits, timeouts, connection errors) are retried
  with exponential backoff via `tenacity`; each provider SDK's exception
  types are collected lazily so the module still imports if only one
  provider's package is installed.
- Provider SDK client construction uses local imports (not module-level),
  which doubles as the seam that makes `build_chat_model` mockable per
  provider in tests without needing real API keys.
- Tests: missing-key error path for all three providers, correct client
  construction with the right model name per provider, and the
  `generate_text`/`generate_structured` wrapper logic against a fake model.

### Added — Step 4: Transcript extraction (multi-language, translation)
- `app/services/youtube_transcript_fetcher.py`: wraps
  `youtube-transcript-api`, preferring a manually-created transcript in the
  requested language, falling back to auto-generated captions, then to
  whatever language is available at all — translating to English when the
  source isn't English and YouTube offers a translation for it.
- Wraps `TranscriptsDisabled`, `VideoUnavailable`, and
  `CouldNotRetrieveTranscript` as `ExternalServiceError` so the API never
  leaks a raw library exception.
- `app/repositories/transcript_repository.py` +
  `app/services/transcript_service.py`: get-or-fetch-and-persist, one
  transcript row per video (whichever language ends up used downstream).
- `GET /api/v1/transcript?url=...&language=...&translate_to_english=...`
  (`app/api/v1/endpoints/transcript.py`), resolving the video via
  `VideoService` first.
- Tests: 7 fetcher-logic cases (manual/auto-generated fallback, translation
  triggered vs. skipped, all three disabled/unavailable/unretrievable error
  paths), a service test proving the fetcher is skipped when a transcript
  is already stored, and an API test with the DB dependency overridden.

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

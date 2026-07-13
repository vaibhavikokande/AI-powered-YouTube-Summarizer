# Changelog

All notable changes to this project are documented here.
Format loosely follows [Keep a Changelog](https://keepachangelog.com/).

## [Unreleased]

### Added — Step 9: Auth (JWT + Google OAuth), dashboard/history
- `app/core/security.py`: password hashing (`passlib`/bcrypt), JWT access
  (60 min) + refresh (7 day) token creation/decoding (`python-jose`).
- `app/services/google_oauth_service.py`: verifies a Google Identity
  Services ID token by validating its signature against Google's public
  JWKS (via `authlib`) — deliberately avoids the `google-auth` SDK, since
  an ID token is just a standard JWT. JWKS-fetching is a separate method
  specifically so it can be mocked without needing to fake an async HTTP
  context manager in tests.
- `app/services/auth_service.py`: register, authenticate, Google login
  (auto-links to an existing password account by email on first Google
  login, or creates a new user), and refresh-token rotation.
- `app/api/deps.py`: `get_current_user`/`get_current_user_optional` FastAPI
  dependencies. `/video`, `/summarize`, `/chat`, and `/notes` now accept an
  optional bearer token — they still work anonymously, but attribute the
  action to the caller when authenticated.
- `POST /register`, `POST /login`, `POST /login/google`, `POST /refresh`,
  `GET /me` (`app/api/v1/endpoints/auth.py`).
- **Design fix caught before it shipped:** initially wired history/search
  around `Video.created_by_user_id`, but `Video` rows are deduplicated
  *globally* by `youtube_video_id` — a single-owner column can't represent
  "in my history" once a second user summarizes a video someone else
  already looked up. Replaced with a `HistoryEntry` join table
  (`user_id`, `video_id`, unique constraint, `updated_at` as "last
  viewed") — migration `0003`. `GET /history` now covers History, Recently
  Summarized, and Search (by title) with one query, since they're the same
  underlying data.
- **Security fix caught in the same pass:** `ChatService.get_or_create_session`
  accepted any `session_id` without checking ownership — a logged-in user
  could continue another authenticated user's chat session just by knowing
  (or guessing) its UUID. Now raises `ForbiddenError` unless the session is
  anonymous or owned by the requesting user.
- Favorites (`GET/POST/DELETE /favorites`) and Bookmarks
  (`GET/POST /bookmarks`, `DELETE /bookmarks/{id}`) — thin services over
  the `Favorite`/`Bookmark` models from Step 2; bookmark deletion checks
  ownership (`ForbiddenError` for another user's bookmark).
- Tests: JWT round-trip + tamper rejection, `AuthService` (register,
  authenticate, all three Google-login paths, refresh), `GoogleOAuthService`
  (not-configured, valid, wrong-audience, JOSE-error-wrapping),
  `get_current_user`/`get_current_user_optional`, and service + API tests
  for history, favorites, and bookmarks.

### Added — Step 8: Content generators (mind map, FAQ, flashcards, quiz, notes)
- **Refactor carried over from Step 6:** extracted the map-step (chunking +
  per-chunk summarization) out of `SummarizationService` into a new shared
  `app/services/content_prep_service.py`, whose output is now cached on
  `Transcript.chunk_summaries_text` (migration `0002`). Every generator in
  this step builds on the same cached text — asking for flashcards after
  already generating a summary (or vice versa) no longer re-runs the LLM
  map step. This also fixed a real inefficiency in Step 6: key
  takeaways/topics/timestamped sections were being re-derived via fresh LLM
  calls every time a *new* summary type was requested for a video that
  already had one — they're video-level properties, not summary-type-level,
  so they're now derived once and reused across every additional summary
  type (`SummarizationService.summarize()`).
- New `FAQItem` model + `faq_items` table (migration `0002`) — the other
  three generators (flashcards, quiz, notes) already had models from Step 2.
- `POST /api/v1/faq`, `POST /api/v1/flashcards`, `POST /api/v1/quiz`,
  `POST /api/v1/notes` — each resolves video → transcript → cached combined
  summary → structured LLM generation → persists once (idempotent: a
  second call for the same video returns the existing rows rather than
  regenerating).
- Quiz generation supports mixed MCQ/true-false/fill-in-the-blank in one
  request (`app/prompts/quiz_prompts.py`), with type-specific formatting
  rules (e.g. true/false and fill-blank must have `options: null`).
- Mind map generation (`include_mindmap` on `POST /summarize`) fills in the
  `Summary.mindmap_markdown` field added back in Step 2, as Markdown nested
  bullets — reuses the same `Summary` row rather than a new resource, since
  no dedicated endpoint for it was in the original spec's endpoint list.
- Tests: `ContentPrepService` cache-hit/cache-miss behavior, rewritten
  `SummarizationService` tests covering first-summary derivation vs.
  reuse-on-additional-type vs. skip-when-cached vs. mindmap backfill, and
  service + API tests for all four new generators.

### Added — Step 7: RAG pipeline (chat with the video)
- `app/vector_store/embeddings.py`: `sentence-transformers` model loaded
  once per process (`lru_cache`); blocking `.encode()` calls run via
  `asyncio.to_thread`.
- `app/vector_store/chroma_client.py`: one ChromaDB collection per video
  (`video_{video_id}`), so retrieval never crosses between videos. Raises
  `NotImplementedError` if `VECTOR_STORE_PROVIDER` is ever set to
  `pinecone`, since only Chroma is implemented (matches the MVP decision
  from Step 1) — rather than silently ignoring the setting.
- `app/services/rag_service.py`: indexes a transcript into Chroma using
  smaller ~1500-char chunks than summarization's ~6000-char chunks (finer
  retrieval granularity), skipping re-indexing if a video's collection is
  already populated; retrieves top-k relevant chunks for a question.
- `LLMProvider.stream_text()` added to the Step 5 abstraction —
  `.astream()` under the hood, deliberately *not* wrapped in the retry
  logic (retrying mid-stream would duplicate output already sent to the
  client).
- `app/services/chat_service.py`: builds the RAG prompt (system message
  with retrieved context + full prior conversation history as alternating
  Human/AI messages + the new question), streams the answer, and persists
  both sides of the exchange only after the full answer is assembled.
- `POST /api/v1/chat` (`app/api/v1/endpoints/chat.py`) streams Server-Sent
  Events (`data: {"token": "..."}` per token, then a final
  `data: {"session_id": "...", "done": true}` so the client can continue
  the same conversation).
- Tests: 5 RAG-service cases (skip-when-indexed, embed-and-add, empty
  retrieval, result mapping), a streaming test for `LLMProvider.stream_text`
  (verifying empty chunks are filtered), 5 chat-service cases (session
  resolution — found/not-found/created — and full ask() flow verifying
  call order and persisted content), and an SSE-parsing API test.

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

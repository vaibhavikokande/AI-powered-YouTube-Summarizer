# Architecture

> Status: Step 14 (CI/CD + cloud deployment config) complete. This document is updated as each
> subsequent build step lands — see [CHANGELOG.md](../CHANGELOG.md).

## 1. System overview

The app is a Clean Architecture monorepo with two independently deployable
services plus supporting infrastructure:

```
┌─────────────┐      HTTPS       ┌──────────────┐
│  frontend    │ ───────────────▶ │   backend    │
│  React SPA   │ ◀─────────────── │   FastAPI    │
└─────────────┘   JSON / SSE      └──────┬───────┘
                                          │
                 ┌────────────────────────┼────────────────────────┐
                 ▼                        ▼                        ▼
          ┌─────────────┐        ┌───────────────┐        ┌───────────────┐
          │ PostgreSQL   │        │ Redis          │        │ ChromaDB      │
          │ (system of   │        │ (cache, Celery │        │ (vector store │
          │  record)     │        │  broker/queue) │        │  for RAG)     │
          └─────────────┘        └───────────────┘        └───────────────┘
                                          │
                                          ▼
                                 ┌────────────────┐
                                 │ Celery workers  │
                                 │ (long-running   │
                                 │  AI jobs)       │
                                 └────────────────┘
                                          │
                                          ▼
                                 ┌────────────────┐
                                 │ LLM provider    │
                                 │ Claude / OpenAI │
                                 │ / Gemini        │
                                 │ (configurable)  │
                                 └────────────────┘
```

## 2. Backend folder structure (Clean Architecture)

```
backend/app/
├── main.py            # FastAPI app factory, middleware, exception handlers
├── core/               # Cross-cutting concerns: config, logging, exceptions, security
├── api/v1/             # HTTP layer only — routers + endpoint functions, no business logic
│   └── endpoints/
├── schemas/            # Pydantic request/response DTOs (API contract)
├── models/             # SQLAlchemy ORM models (persistence contract)
├── repositories/        # Data access layer — only place that talks to the DB session
├── services/           # Business logic, orchestration; depends on repositories, not the other way around
├── agents/             # LangChain/LangGraph agent + chain definitions
├── prompts/             # Versioned prompt templates, kept out of service code
├── vector_store/         # Embedding + ChromaDB/Pinecone client abstraction
├── middleware/          # Rate limiting, request logging, auth middleware
├── utils/               # Pure, stateless helper functions
└── db/                  # Engine/session setup, Alembic wiring
```

**Dependency rule:** `api` → `services` → `repositories` → `models`. Services
never import from `api`; repositories never import from `services`. This keeps
business logic testable without spinning up FastAPI or a real database.

## 3. Data flow: summarize a video (high level)

**Fast, synchronous endpoints** (return within the request):

0. `GET /api/v1/video?url=...` validates the URL (`app/utils/youtube.py`) and
   returns metadata, fetched via **yt-dlp** (`app/services/metadata_service.py`)
   rather than the official YouTube Data API — this avoids requiring a Google
   Cloud project/API key/quota just to try the app. Videos are deduplicated
   by `youtube_video_id`, so re-submitting the same URL reuses the stored row
   instead of re-fetching. Cached in Redis by video id (§6.1) since this is
   the app's highest-traffic read.
0.5. `GET /api/v1/transcript?url=...` (`app/services/transcript_service.py` +
   `app/services/youtube_transcript_fetcher.py`) fetches captions via
   `youtube-transcript-api`: manually-created in the requested language →
   auto-generated in that language → whatever's available — translating to
   English only when the source isn't English already. One transcript row
   is kept per video (the language actually used downstream), with
   `is_auto_generated`/`is_translated`/`source_language` flags so the UI can
   show e.g. "auto-translated from Spanish."
4. `POST /api/v1/chat` (`app/services/chat_service.py`) indexes the video
   into ChromaDB on first use (`RagService.ensure_indexed`, a no-op if
   already indexed), retrieves the top-k most relevant chunks for the
   question, builds a prompt with full prior conversation history as
   alternating Human/AI messages, and streams the answer back as SSE —
   persisting both sides of the exchange once the full answer is assembled.
   Stays synchronous even after Step 11: an SSE stream needs a live
   connection to push tokens over, which the job-queue model below doesn't
   fit — there's nothing to "poll" mid-stream.

**Background-job endpoints** (Step 11 — enqueue and return a `task_id`
immediately; see §6.1):

1. `POST /api/v1/summarize`, `POST /api/v1/quiz`, `POST /api/v1/flashcards`,
   `POST /api/v1/faq`, `POST /api/v1/notes` all validate the URL synchronously
   (fail fast on a malformed URL before enqueuing — `extract_video_id()` is
   cheap, no need to round-trip through Celery for a 422), then enqueue a
   Celery task (`app/tasks/content_tasks.py`) and return
   `{"task_id": "...", "status": "queued"}`.
2. Each task opens its own DB session (a worker is a separate process from
   the FastAPI app) and runs the exact same service pipeline the endpoint
   used to run inline — `VideoService` → `TranscriptService` →
   `SummarizationService`/`QuizService`/etc. — then serializes the result to
   a plain dict (`app/tasks/serialization.py`), since Celery's JSON result
   backend can't serialize ORM objects/UUIDs/enums/datetimes directly.
3. `GET /api/v1/jobs/{task_id}` (`app/api/v1/endpoints/jobs.py`) polls
   Celery's result backend (Redis) for status/result — no separate job-status
   table needed, since Celery already persists this.
4. Summarization's map-reduce (`app/services/summarization_service.py` +
   `app/utils/chunking.py`) is unchanged by this move: chunk the transcript,
   summarize each chunk independently (concurrently, via `asyncio.gather`),
   combine into each requested summary type, deriving key
   takeaways/topics/timestamped sections once and reusing them across
   summary types — all of that now just runs inside the task instead of
   inline in the request handler.

## 4. RAG flow

Implemented in `app/vector_store/` (embeddings + Chroma client) and
`app/services/rag_service.py` + `app/services/chat_service.py`:

```
Transcript
   │  (chunk_transcript(), ~1500-char chunks — finer-grained than the
   │   ~6000-char chunks Step 6's summarizer uses, for precise retrieval)
   ▼
Chunks
   │  (sentence-transformers "all-MiniLM-L6-v2", run via asyncio.to_thread)
   ▼
Embeddings ──▶ ChromaDB collection "video_{video_id}" (one per video)
   │
   ▼
Retriever (top-k cosine/L2 similarity via collection.query — no MMR yet)
   │
   ▼
LLM (provider from LLM_PROVIDER) + full prior ChatMessage history as context
   │
   ▼
Answer streamed token-by-token over SSE; both messages persisted after
```

Indexing happens lazily on the first chat message for a video (not
eagerly during summarization) and is skipped on every later message once
`collection.count() > 0` — so multi-turn conversations only pay the
embedding cost once per video.

### 4.1 LLM provider abstraction

Implemented in `backend/app/agents/llm_provider.py`. Every AI feature
(summarization, quizzes/flashcards/FAQ, RAG chat) calls `LLMProvider` —
never a provider SDK directly:

```
Settings.LLM_PROVIDER ("claude" | "openai" | "gemini")
   │
   ▼
build_chat_model() ── selects ChatAnthropic / ChatOpenAI / ChatGoogleGenerativeAI
   │                   (raises ExternalServiceError if that provider's API key is missing)
   ▼
LLMProvider
   ├── generate_text(messages) -> str
   └── generate_structured(messages, schema) -> schema instance
          (LangChain `with_structured_output` — same call shape on all 3 providers)
   │
   ▼
tenacity retry (3 attempts, exponential backoff) on rate-limit/timeout/connection errors
```

Switching providers is a one-line `.env` change (`LLM_PROVIDER=openai`) —
no code in any service changes. Provider SDK classes are imported inside
`build_chat_model()` (not at module load) specifically so tests can mock
`ChatAnthropic`/`ChatOpenAI`/`ChatGoogleGenerativeAI` per-provider without
needing real API keys.

### 4.2 Content generation & the shared map step

Summaries, FAQ, flashcards, quiz, notes, and mind maps all need the same
starting material: the transcript's chunks, each summarized once. Rather
than every generator re-running that map step, `app/services/content_prep_service.py`
computes it once and caches the result on `Transcript.chunk_summaries_text`:

```
                         ┌─────────────────────────┐
                         │ ContentPrepService        │
Transcript ─────────────▶│  .get_combined_summary()  │──▶ combined chunk-summary text
                         │  (cache hit: return text  │      │
                         │   from chunk_summaries_   │      │  used by all six generators:
                         │   text; cache miss:       │      ▼
                         │   chunk + map + persist)  │  Summary content (per type) · KeyTakeaways ·
                         └─────────────────────────┘  Topics · Mind map · FAQ · Flashcards · Quiz · Notes
```

`SummarizationService` additionally derives `key_takeaways`/`topics`/
`timestamped_sections` only on a video's *first* summary ever generated
(they describe the video, not a specific summary type) and reuses them
from that first `Summary` row for every later summary type requested —
avoiding both redundant LLM calls and the risk of two summary rows for the
same video disagreeing on takeaways/topics due to LLM non-determinism.

### 4.3 Export, sharing, and voice summary

- **Export** (`app/services/export_service.py`) has no shared "renderer"
  abstraction across PDF/DOCX/Markdown/TXT — each format is built directly
  from the `Summary` row's fields. That's deliberate: unifying them behind
  one intermediate representation would be premature complexity for four
  formats with genuinely different constraints (reportlab's `Paragraph`
  parses input as XML-like markup and must be escaped; `python-docx` wants
  `Document.add_heading`/`add_paragraph(style=...)` calls; Markdown/TXT are
  just string building). All four are exercised in tests against the real
  libraries (parsing the DOCX back, checking the PDF's `%PDF` magic bytes)
  rather than mocked, since the risk here is in the libraries' actual
  output, not orchestration logic.
- **Sharing**: `POST /share` mints an unguessable token
  (`secrets.token_urlsafe`); `GET /share/{token}` is intentionally the only
  *public, unauthenticated* endpoint that returns user content, since a
  share link's entire purpose is working for someone without an account.
- **Voice summary**: generated on demand via `gTTS` rather than
  pre-generated and stored — there's no blob storage in this stack yet
  (Step 14's cloud deployment doesn't add one), and regenerating a few
  KB of audio per request is cheap enough not to need it.

## 5. Database schema

Implemented in `backend/app/models/` (SQLAlchemy 2.0, `Mapped`/`mapped_column`
style) and `backend/alembic/versions/` (`0001_initial_schema.py`,
`0002_add_faq_and_chunk_summaries.py` — adds `faq_items` and
`transcripts.chunk_summaries_text`, see §4.2 — and
`0003_add_history_entries.py`, see below).

```
users ──< videos (created_by_user_id, nullable — anonymous summarize allowed)
videos ──< transcripts        (one row per language fetched; caches chunk_summaries_text)
videos ──< summaries          (one row per summary_type: short/medium/detailed/bullet)
videos ──< flashcards
videos ──< quizzes ──< quiz_questions
videos ──< notes
videos ──< faq_items
videos ──< chat_sessions ──< chat_messages
videos ──< favorites >── users            (whole-video favorite, unique per user+video)
videos ──< bookmarks >── users            (saved timestamp + optional note within a video)
videos ──< history_entries >── users      (per-user "viewed" record, unique per user+video)
summaries ──< share_links     (token-based public share link, optional expiry)
```

Design notes:

- **`Video` is deduplicated by `youtube_video_id`** (unique index) — summarizing
  the same URL twice reuses the existing row rather than duplicating metadata.
- **History is a separate join table (`history_entries`), not `Video.created_by_user_id`.**
  Because `Video` rows are global (one per YouTube video, shared by every
  user), a single-owner column can't represent "this is in my history" once
  a second user summarizes a video someone else already looked up.
  `HistoryEntry(user_id, video_id)` with a unique constraint and
  `updated_at`-as-"last viewed" is `Video.created_by_user_id`'s per-user
  analogue — the same pattern `Favorite`/`Bookmark` already used, applied
  to viewing rather than favoriting.
- **JSONB columns** (`transcripts.segments`, `summaries.key_takeaways`,
  `summaries.timestamped_sections`, `summaries.topics`,
  `quiz_questions.options`) hold structured LLM output that doesn't need its
  own relational table — see `docs/SPEC.md` for the corresponding Pydantic
  shapes.
- **Enums are stored as `VARCHAR` + a `CHECK` constraint** (`native_enum=False`)
  rather than native Postgres enum types, since adding a new enum value to a
  native Postgres enum requires a non-transactional `ALTER TYPE`, which is
  more disruptive than a migration that updates a `CHECK` constraint.
- **`ON DELETE CASCADE`** from `videos` down to transcripts/summaries/etc., and
  **`ON DELETE SET NULL`** from content back to `users`, so deleting a user
  never silently deletes videos/summaries other users may also reference.
- A single naming convention (`backend/app/db/base.py`) generates predictable
  constraint/index names (e.g. `uq_favorites_user_video`,
  `ck_summaries_summary_type`) so later migrations can reference them by name.

## 6. Background jobs, caching, rate limiting, retries

### 6.1 Background jobs (Celery)

`app/services/celery_app.py` configures the Celery app (Redis broker +
result backend, both already used by the app's other Redis needs);
`app/tasks/content_tasks.py` holds the five tasks. The Celery app uses
`include=["app.tasks.content_tasks"]` rather than `autodiscover_tasks()` —
autodiscover looks for a submodule literally named `tasks` inside each
listed package (i.e. `app.tasks.tasks`), which isn't this project's layout.

```
Endpoint (e.g. POST /summarize)
   │  extract_video_id() — fail fast on a malformed URL, no Celery round-trip for a 422
   ▼
task.delay(...) → Redis (broker)
   │                                    202-style response: {"task_id", "status": "queued"}
   ▼
Celery worker (separate process)
   │  opens its own AsyncSession (can't reuse the request's session across processes)
   ▼
Same service pipeline the endpoint used to call inline
   │
   ▼
Result serialized to a plain dict (app/tasks/serialization.py — Celery's
JSON backend can't serialize ORM objects/UUIDs/enums/datetimes) → Redis (backend)
   │
   ▼
GET /jobs/{task_id} reads status/result straight from the result backend
```

No separate "jobs" database table was added — Celery's result backend
already persists task state, and duplicating that in Postgres would just be
two sources of truth to keep in sync.

### 6.2 Caching

`app/core/cache.py` wraps `redis.asyncio` with JSON get/set helpers. Applied
to `GET /video`: a trending video's metadata gets requested repeatedly by
many different users, so it's cached by video id (1 hour TTL) as a tier in
front of Postgres, checked before `VideoService` runs. A cache hit implies
the row already exists in Postgres (the cache is only populated *after* a
successful DB write), so downstream FK operations (like recording a
`GET /history` view) stay safe on a cache hit. The same pattern generalizes
to any other read-heavy endpoint if traffic patterns call for it later.

### 6.3 Rate limiting

`app/middleware/rate_limit.py` configures a `slowapi` `Limiter` keyed by
client IP, with `RATE_LIMIT_PER_MINUTE` (default 30/min) as the app-wide
default. The five content-generation endpoints — the most LLM-cost-heavy
ones — get a tighter `10/minute` limit via `@limiter.limit(...)` on top of
that default.

### 6.4 Retries

Two independent retry layers, deliberately not merged into one:

- **LLM-call level** (`app/agents/llm_provider.py`, since Step 5): retries a
  single provider API call on rate-limit/timeout/connection errors.
- **Task level** (`app/tasks/content_tasks.py`, this step): retries an
  entire task on `ExternalServiceError`/`ConnectionError`/`TimeoutError`/
  `OSError` — genuinely transient infra failures — with exponential backoff
  and jitter, scoped deliberately to exclude `ValidationAppError`/
  `NotFoundError`, where retrying identical bad input just delays an
  inevitable identical failure.

## 7. CI/CD & Deployment

**CI** (`.github/workflows/backend-ci.yml`, `frontend-ci.yml`,
`docker-build.yml`) runs on every push/PR: backend lint
(ruff/black/mypy) + unit/API tests against mocks + integration tests
against real Postgres/Redis service containers + Alembic migration
check; frontend typecheck/lint/test/build; both Dockerfiles built (not
pushed) to catch breakage early. This is the first point in the project
where the ~50 backend tests accumulated since Step 1 actually run, since
GitHub's runners have Python and this development machine didn't.

**CD** (`.github/workflows/deploy.yml`) is gated behind a repository
variable (`ENABLE_DEPLOY`), not just secret presence — so wiring up CI/CD
doesn't immediately attempt (and fail) a deployment before Railway/Vercel
projects exist. See the README's Deployment section for the full setup
walkthrough.

- **Local development:** `docker-compose up` runs Postgres, Redis, ChromaDB,
  the FastAPI backend (with `--reload`), a Celery worker, and the Vite dev
  server together.
- **Production:** backend + Celery worker deploy to Railway as two services
  from the same Dockerfile (`backend/railway.toml`), differing only in
  start command; frontend deploys to Vercel (`frontend/vercel.json` adds
  the SPA rewrite client-side routing needs). The frontend calls the
  backend via `VITE_API_BASE_URL` in production (no dev-server proxy
  exists outside `vite dev`) — see `frontend/src/services/api.ts`.
- Postgres/Redis are Railway-managed add-ons in production.

## 8. Security

- **Passwords**: hashed with bcrypt (`passlib`), never logged or returned in
  any response schema.
- **JWT**: short-lived access tokens (60 min) + longer refresh tokens (7
  days), both HS256-signed with `JWT_SECRET_KEY` (must be overridden outside
  local dev — see `.env.example`). `app/api/deps.py` verifies the token
  type (`access` vs `refresh`) so a refresh token can't be used to call
  protected endpoints directly.
- **Google OAuth**: `app/services/google_oauth_service.py` verifies the ID
  token's signature against Google's JWKS and checks `aud`/`iss` — a
  forged or third-party-app token is rejected before any user lookup.
- **Authorization, not just authentication**: `ChatService` rejects
  continuing another user's chat session (`ForbiddenError`); `BookmarkService`
  rejects deleting another user's bookmark. Ownership is checked at the
  service layer, not assumed from a valid token alone.
- **Anonymous-first, personalized-when-logged-in**: `/video`, `/summarize`,
  `/chat`, and `/notes` use `get_current_user_optional` — they work without
  an account (matching the "no login wall" UX most summarizer tools have)
  but attribute history/ownership when a token is present.
- **Rate limiting** (per-IP, §6.3) and CORS allow-list (`app/main.py`) are
  in place; secrets-via-env-only is covered further in Step 14's deployment
  pipeline.

## 9. Frontend architecture

```
frontend/src/
├── types/api.ts            # TypeScript interfaces mirroring every backend Pydantic schema
├── lib/
│   ├── api-client.ts         # One typed function per endpoint (axios)
│   └── utils.ts               # cn() — clsx + tailwind-merge, the standard ShadCN helper
├── store/auth-store.ts        # Zustand: user, isAuthenticated, tokens in localStorage
├── hooks/
│   ├── useContentJob.ts        # Shared request → enqueue → poll → result lifecycle (§6.1)
│   └── useAuth.ts               # Bootstraps the current user from a stored token on load
├── components/
│   ├── ui/                       # Button/Card/Input/Tabs/Badge/Spinner — hand-built ShadCN-style
│   ├── layout/Header.tsx
│   ├── video/VideoCard.tsx
│   ├── summary/SummaryPanel.tsx    # Tabs across all 4 summary types from one job result
│   ├── chat/ChatPanel.tsx          # SSE streaming via raw fetch()
│   └── generators/                  # QuizPanel, FlashcardsPanel, FAQPanel, NotesPanel
└── pages/                            # HomePage, LoginPage, RegisterPage, HistoryPage
```

Two implementation notes worth calling out:

- **`useContentJob`** is the one abstraction every job-based generator shares:
  it wraps the enqueue call, then polls `GET /jobs/{task_id}` on a
  `refetchInterval` that stops once the job reaches `SUCCESS`/`FAILURE`.
  `SummaryPanel`, `QuizPanel`, `FlashcardsPanel`, `FAQPanel`, and
  `NotesPanel` are each a thin wrapper around it with their own request
  function and result rendering — this is the "three similar lines is
  better than a premature abstraction" line drawn at the boundary between
  generic lifecycle (shared) and content-specific rendering (not shared).
- **ShadCN components are hand-written**, not generated by the ShadCN CLI —
  that CLI needs an interactive prompt this environment can't run. They
  follow the identical pattern the CLI itself would produce (Radix
  primitives + `class-variance-authority` variants + `tailwind-merge` via
  `cn()`), so swapping in CLI-generated versions later is a drop-in
  replacement, not a rewrite.

**Verification caveat:** with no backend runnable in this environment
(Steps 1–11 remained unexecuted throughout), the frontend was exercised
against a backend that returns proxy errors for every API call. This
confirmed: correct request construction (URLs, params, headers), graceful
error-state rendering, client-side routing, dark mode, and TypeScript
type-checking (`tsc --noEmit` clean) — but not the actual success-path
rendering of real summaries/quizzes/chat streams, which needs a live
backend to verify.

# Architecture

> Status: Step 2 (database models & migrations) complete. This document is updated as each
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

1. `POST /api/v1/summarize` validates the URL and enqueues a Celery job (long
   transcripts can take minutes to process — never block the request thread).
2. Worker pipeline: fetch metadata → fetch transcript → chunk transcript →
   summarize (map-reduce over chunks) → extract topics/takeaways → persist.
3. Frontend polls (or subscribes via SSE) for job status and renders results
   as they become available.
4. Transcript chunks are simultaneously embedded and written to ChromaDB so
   the "chat with this video" (RAG) feature works immediately after.

*(Full sequence diagrams are added in Step 6/7 once the summarization and RAG
services exist.)*

## 4. RAG flow

```
Transcript
   │  (semantic chunking, ~500–1000 tokens/chunk with overlap)
   ▼
Chunks
   │  (sentence-transformers embeddings)
   ▼
Embeddings ──▶ ChromaDB (namespaced per video_id)
   │
   ▼
Retriever (top-k similarity + optional MMR)
   │
   ▼
LLM (provider from LLM_PROVIDER) + conversation memory
   │
   ▼
Answer (streamed back to the client)
```

## 5. Database schema

Implemented in `backend/app/models/` (SQLAlchemy 2.0, `Mapped`/`mapped_column`
style) and `backend/alembic/versions/0001_initial_schema.py`.

```
users ──< videos (created_by_user_id, nullable — anonymous summarize allowed)
videos ──< transcripts        (one row per language fetched)
videos ──< summaries          (one row per summary_type: short/medium/detailed/bullet)
videos ──< flashcards
videos ──< quizzes ──< quiz_questions
videos ──< notes
videos ──< chat_sessions ──< chat_messages
videos ──< favorites >── users            (whole-video favorite, unique per user+video)
videos ──< bookmarks >── users            (saved timestamp + optional note within a video)
summaries ──< share_links     (token-based public share link, optional expiry)
```

Design notes:

- **`Video` is deduplicated by `youtube_video_id`** (unique index) — summarizing
  the same URL twice reuses the existing row rather than duplicating metadata.
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

## 6. Deployment

- **Local development:** `docker-compose up` runs Postgres, Redis, ChromaDB,
  the FastAPI backend (with `--reload`), a Celery worker, and the Vite dev
  server together.
- **Production:** backend + Celery worker deploy to Railway (Dockerfile-based),
  frontend deploys to Vercel, Postgres/Redis are managed add-ons. Details and
  pipeline are added in Step 14.

## 7. Security

Covered in depth once auth (Step 9) and CI/CD (Step 14) land: JWT access +
refresh tokens, Google OAuth, per-IP rate limiting, strict Pydantic input
validation, secrets via environment variables only (never committed — see
`.env.example` files), CORS allow-list.

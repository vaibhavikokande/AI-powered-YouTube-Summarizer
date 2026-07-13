# Engineering Spec

Ground rules for anyone (including future-you) contributing to this codebase.

## Coding standards

- **Python:** type hints on every function signature; `ruff` + `black`
  (line length 100) + `mypy --disallow-untyped-defs` must pass before commit.
- **TypeScript:** `strict: true`, no `any` without a `// eslint-disable` and a
  comment explaining why.
- Prefer `async def` end-to-end in the backend — sync DB calls or blocking I/O
  inside an async endpoint block the whole event loop.
- No business logic in `api/` route handlers — they parse input, call a
  service, return a schema. Full stop.
- Comments explain *why*, not *what*. If a comment restates the code, delete it.

## Naming conventions

| Item | Convention | Example |
|---|---|---|
| Python modules/files | `snake_case` | `transcript_service.py` |
| Python classes | `PascalCase` | `TranscriptService` |
| Python functions/vars | `snake_case` | `get_video_metadata()` |
| SQLAlchemy models | singular `PascalCase` | `class Video(Base)` |
| DB tables | plural `snake_case` | `videos`, `chat_messages` |
| Pydantic schemas | `PascalCase` + suffix | `VideoCreate`, `VideoResponse` |
| React components | `PascalCase` | `SummaryCard.tsx` |
| React hooks | `useCamelCase` | `useVideoSummary.ts` |
| API routes | singular noun or verb, matching the feature name | `/api/v1/summarize`, `/api/v1/video` |
| Env vars | `SCREAMING_SNAKE_CASE` | `LLM_PROVIDER` |

## Folder rules

- A file goes in `services/` only if it orchestrates business logic across
  more than one repository/external client. If it's a single DB query, it
  belongs in `repositories/`.
- `prompts/` holds only prompt template strings/functions — no LLM calls.
- Anything importing `sqlalchemy` outside `models/`, `repositories/`, or
  `db/` is a smell — stop and reconsider.
- Frontend `components/` are presentational; data fetching lives in
  `hooks/` (wrapping React Query) or `services/`.

## Prompt engineering guidelines

- Every prompt template lives in `app/prompts/` as a named function returning
  a string (or a LangChain `PromptTemplate`), never inlined in a service.
- Use **structured output** (Pydantic schema via `.with_structured_output()`
  or provider JSON mode) for anything the frontend will render as data —
  summaries, quizzes, flashcards, FAQs. Free-text-only for chat answers.
- Long transcripts use **map-reduce**: chunk → per-chunk summary → reduce
  pass over chunk summaries. Never stuff a multi-hour transcript into a
  single prompt.
- Every prompt that produces user-facing structured data must have an
  explicit "if the transcript doesn't contain X, return an empty list/null"
  instruction — the model must not hallucinate quotes/stats/definitions that
  aren't in the source.
- Include the video's language and requested output language explicitly in
  every prompt; never assume English.

## API standards

- All endpoints are versioned under `/api/v1`.
- Request/response bodies are always Pydantic models — no raw dicts.
- Errors return `{"error": {"code": "...", "message": "..."}}` (see
  `app/core/exceptions.py`) with an appropriate HTTP status — never a bare
  500 with a stack trace leaked to the client.
- Long-running work (summarization, quiz/flashcard generation) is always
  asynchronous: the endpoint enqueues a job and returns a job/task id;
  results are fetched via a status endpoint or pushed via SSE. Never block
  an HTTP request on an LLM call that might take minutes.
- Pagination on all list endpoints (`history`, `search`) via `limit`/`offset`
  query params, capped server-side (max `limit=100`).

## Testing strategy

- **Unit tests** (`tests/unit/`): services and utils with all I/O mocked.
- **Integration tests** (`tests/integration/`): repository layer against a
  real (test) Postgres via `pytest-asyncio` + a transactional rollback per
  test. The `db_session` fixture (`tests/integration/conftest.py`) binds the
  session to a connection with `join_transaction_mode="create_savepoint"` —
  repository code calling `session.commit()` only commits a SAVEPOINT, so the
  fixture's outer rollback still undoes everything afterward. Marked
  `@pytest.mark.integration` and skipped (not errored) when no Postgres is
  reachable — run `docker compose up postgres` first, then `pytest -m integration`.
- **API tests**: FastAPI `TestClient`/`httpx.AsyncClient` hitting real routes
  with the DB/vector-store dependencies overridden via `app.dependency_overrides`.
- **Frontend tests** (`frontend/src/**/*.test.{ts,tsx}`): Vitest + React
  Testing Library. Explicit `afterEach(cleanup)` in `src/test/setup.ts` —
  don't rely on `@testing-library/react`'s auto-cleanup, which only
  registers itself when it detects a global `afterEach` (this project
  doesn't set `globals: true`, so it silently wouldn't have fired).
- External calls (YouTube, LLM providers) are always mocked/recorded in tests
  — tests must never make real network calls to paid APIs.
- Minimum bar before merging a feature step: the happy path + one failure
  path (e.g. private/unavailable video, transcript missing) per endpoint.

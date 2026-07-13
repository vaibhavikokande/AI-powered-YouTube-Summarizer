# Changelog

All notable changes to this project are documented here.
Format loosely follows [Keep a Changelog](https://keepachangelog.com/).

## [Unreleased]

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

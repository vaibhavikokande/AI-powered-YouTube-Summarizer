"""Shared fixtures for integration tests: repositories exercised against a
real Postgres connection (see docs/SPEC.md's testing strategy), instead of
the mocked sessions everywhere else in the suite.

Skips gracefully (rather than erroring) when no Postgres is reachable, so
`pytest` alone still works in environments without one running — run
`docker compose up postgres` first to actually exercise these.
"""

import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from app.core.config import get_settings
from app.db.base import Base
from app.models import *  # noqa: F401,F403 -- registers every model on Base.metadata


@pytest_asyncio.fixture(scope="session")
async def _engine():
    settings = get_settings()
    engine = create_async_engine(settings.DATABASE_URL)

    try:
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
    except Exception as exc:  # noqa: BLE001 -- environment-availability check, not a test assertion
        pytest.skip(f"No Postgres reachable at {settings.DATABASE_URL}: {exc}")

    yield engine
    await engine.dispose()


@pytest_asyncio.fixture
async def db_session(_engine):
    """A session whose transaction is rolled back after the test.

    Repository code calls `session.commit()` internally (see e.g.
    VideoRepository.create). Binding the session to the connection with
    `join_transaction_mode="create_savepoint"` means those commits only
    commit a SAVEPOINT — the outer transaction we roll back below still
    undoes everything the test wrote, so tests never leave data behind or
    see each other's rows.
    """
    async with _engine.connect() as connection:
        await connection.begin()
        session_factory = async_sessionmaker(
            bind=connection, join_transaction_mode="create_savepoint", expire_on_commit=False
        )
        session = session_factory()
        try:
            yield session
        finally:
            await session.close()
            await connection.rollback()

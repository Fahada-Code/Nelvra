import os

import asyncpg
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine

from api.database import get_db
from api.main import app
from api.models.base import Base

# Overridable via env so the suite can run against any local Postgres without
# editing this file. Defaults match the CI postgres service (user/pass: nelvra).
TEST_DATABASE_URL = os.environ.get(
    "TEST_DATABASE_URL", "postgresql+asyncpg://nelvra:nelvra@localhost:5432/nelvra_test"
)
ADMIN_DATABASE_URL = os.environ.get(
    "TEST_ADMIN_DATABASE_URL", "postgresql://nelvra:nelvra@localhost:5432/postgres"
)


@pytest_asyncio.fixture(scope="session", autouse=True)
async def create_test_database():
    """Create the test database if it doesn't already exist."""
    conn = await asyncpg.connect(ADMIN_DATABASE_URL)
    try:
        await conn.execute("CREATE DATABASE nelvra_test")
    except asyncpg.exceptions.DuplicateDatabaseError:
        pass
    finally:
        await conn.close()


@pytest_asyncio.fixture(scope="session")
async def test_engine(create_test_database):
    engine = create_async_engine(TEST_DATABASE_URL, echo=False)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield engine
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await engine.dispose()


@pytest_asyncio.fixture
async def db(test_engine):
    """Each test runs in a rolled-back transaction for isolation."""
    connection = await test_engine.connect()
    transaction = await connection.begin()
    session = AsyncSession(bind=connection, expire_on_commit=False)

    yield session

    await session.close()
    await transaction.rollback()
    await connection.close()


@pytest_asyncio.fixture
async def client(db):
    async def override_get_db():
        yield db

    app.dependency_overrides[get_db] = override_get_db
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
        yield c
    app.dependency_overrides.clear()

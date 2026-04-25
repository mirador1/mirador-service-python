"""Pytest fixtures shared across all tests.

Strategy : SQLite in-memory for unit tests (fast, no Docker), Postgres
testcontainer for integration tests (real DB behavior). Switching is via
the `db_session` fixture variant.
"""

from __future__ import annotations

from collections.abc import AsyncIterator

import pytest_asyncio
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from mirador_service.app import create_app
from mirador_service.db.base import Base, get_db_session


@pytest_asyncio.fixture
async def db_session() -> AsyncIterator[AsyncSession]:
    """In-memory SQLite session — fast, isolated, no Docker.

    Each test gets a fresh schema (CREATE TABLE on connect, DROP after).
    """
    engine = create_async_engine("sqlite+aiosqlite:///:memory:", echo=False)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    factory = async_sessionmaker(bind=engine, class_=AsyncSession, expire_on_commit=False)
    async with factory() as session:
        yield session

    await engine.dispose()


@pytest_asyncio.fixture
async def app(db_session: AsyncSession) -> AsyncIterator[FastAPI]:
    """FastAPI app instance with the test session injected via DI override."""
    app = create_app()

    async def override_db_session() -> AsyncIterator[AsyncSession]:
        # Reuse the test's session — same transaction across the request.
        yield db_session

    app.dependency_overrides[get_db_session] = override_db_session
    yield app
    app.dependency_overrides.clear()


@pytest_asyncio.fixture
async def client(app: FastAPI) -> AsyncIterator[AsyncClient]:
    """httpx async client bound to the test app — no real network."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as c:
        yield c

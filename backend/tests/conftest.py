import os
import sys
from collections.abc import AsyncIterator
from pathlib import Path
from typing import Any

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy import event
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
from sqlalchemy.pool import StaticPool

os.environ.setdefault("POSTGRES_USER", "test")
os.environ.setdefault("POSTGRES_PASSWORD", "test")
os.environ.setdefault("POSTGRES_HOST", "localhost")
os.environ.setdefault("PGPORT", "5432")
os.environ.setdefault("POSTGRES_DB", "test")

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src import app as app_module
from src import service
from src.models import Base


@pytest_asyncio.fixture
async def test_context(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> AsyncIterator[tuple[async_sessionmaker[Any], Path]]:
    engine = create_async_engine(
        "sqlite+aiosqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )

    @event.listens_for(engine.sync_engine, "connect")
    def enable_foreign_keys(dbapi_connection: Any, _: Any) -> None:
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()

    session_maker = async_sessionmaker(engine, expire_on_commit=False)

    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.create_all)

    storage_dir = tmp_path / "storage" / "files"
    storage_dir.mkdir(parents=True)

    monkeypatch.setattr(service, "async_session_maker", session_maker)
    monkeypatch.setattr(service, "STORAGE_DIR", storage_dir)
    monkeypatch.setattr(app_module, "STORAGE_DIR", storage_dir)

    yield session_maker, storage_dir

    await engine.dispose()


@pytest_asyncio.fixture
async def client(test_context: tuple[async_sessionmaker[Any], Path]) -> AsyncIterator[AsyncClient]:
    transport = ASGITransport(app=app_module.app, raise_app_exceptions=False)
    async with AsyncClient(transport=transport, base_url="http://test") as async_client:
        yield async_client

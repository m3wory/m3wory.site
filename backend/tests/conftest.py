from collections.abc import AsyncIterator

import pytest
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient
from sqlalchemy import update

from app.core.config import Settings
from app.db.session import init_db
from app.main import create_app
from app.models.file_record import FileRecord

MAX_FILE_SIZE_MB = 1


@pytest.fixture
async def app(tmp_path) -> AsyncIterator[FastAPI]:
    settings = Settings(
        _env_file=None,
        database_url=f"sqlite+aiosqlite:///{tmp_path / 'test.db'}",
        upload_dir=tmp_path / "uploads",
        max_file_size_mb=MAX_FILE_SIZE_MB,
    )
    app = create_app(settings)
    await init_db(app.state.engine)
    yield app
    await app.state.engine.dispose()


@pytest.fixture
async def client(app: FastAPI) -> AsyncIterator[AsyncClient]:
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        yield client


@pytest.fixture
def upload(client: AsyncClient):
    """Return a coroutine function that uploads a small file and returns the response."""

    async def _upload(
        content: bytes = b"hello",
        filename: str = "hello.txt",
        expires_hours: int = 24,
        max_downloads: int = 0,
    ):
        return await client.post(
            "/api/upload",
            files={"file": (filename, content, "text/plain")},
            data={"expires_hours": expires_hours, "max_downloads": max_downloads},
        )

    return _upload


@pytest.fixture
def update_record(app: FastAPI):
    """Return a coroutine function that changes columns of a stored record directly."""

    async def _update(short_code: str, **values) -> None:
        async with app.state.session_factory() as session:
            await session.execute(
                update(FileRecord).where(FileRecord.short_code == short_code).values(**values)
            )
            await session.commit()

    return _update

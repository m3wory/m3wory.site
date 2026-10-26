from collections.abc import AsyncIterator

from fastapi import Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.repositories.file_repository import FileRepository
from app.services.file_service import FileService


async def get_session(request: Request) -> AsyncIterator[AsyncSession]:
    async with request.app.state.session_factory() as session:
        yield session


def get_file_service(request: Request, session: AsyncSession = Depends(get_session)) -> FileService:
    return FileService(
        repository=FileRepository(session),
        storage=request.app.state.storage,
        max_file_size_bytes=request.app.state.settings.max_file_size_bytes,
    )

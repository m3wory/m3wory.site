import asyncio
import logging
from datetime import datetime

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.core.config import get_settings
from app.db.session import create_engine, create_session_factory
from app.models.file_record import utcnow
from app.repositories.file_repository import FileRepository
from app.services.storage import LocalFileStorage

logger = logging.getLogger("m3wory.cleanup")


async def cleanup_files(
    session_factory: async_sessionmaker[AsyncSession],
    storage: LocalFileStorage,
    now: datetime | None = None,
) -> int:
    """Delete expired or fully-downloaded files from disk and database.

    Returns the number of removed records.
    """
    async with session_factory() as session:
        repository = FileRepository(session)
        records = await repository.list_removable(now or utcnow())
        for record in records:
            storage.delete(record.stored_name)
        await repository.delete_many(records)
    return len(records)


async def main() -> None:
    settings = get_settings()
    engine = create_engine(settings.database_url)
    try:
        removed = await cleanup_files(
            create_session_factory(engine), LocalFileStorage(settings.upload_dir)
        )
    finally:
        await engine.dispose()
    logger.info("Cleaned up %d files.", removed)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="[%(asctime)s] %(message)s")
    asyncio.run(main())

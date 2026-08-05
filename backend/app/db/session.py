from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import declarative_base, sessionmaker

from app.core.config import DATABASE_URL

engine = create_async_engine(DATABASE_URL, echo=False)
AsyncSessionLocal = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
Base = declarative_base()


async def init_db() -> None:
    """
    Initialize database and create all tables.
    Imported models are registered via Base metadata.
    """
    async with engine.begin() as conn:
        # Import here to avoid circular imports
        from app.models.file_record import FileRecord as _FileRecord  # noqa: F401

        await conn.run_sync(Base.metadata.create_all)


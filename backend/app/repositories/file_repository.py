from datetime import datetime

from sqlalchemy import or_, select, update
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.file_record import FileRecord


class FileRepository:
    """Database access for FileRecord. Each mutating method commits its own unit of work."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_by_short_code(self, short_code: str) -> FileRecord | None:
        result = await self._session.execute(
            select(FileRecord).where(FileRecord.short_code == short_code)
        )
        return result.scalar_one_or_none()

    async def add(self, record: FileRecord) -> bool:
        """Insert a record. Returns False if its short_code is already taken."""
        self._session.add(record)
        try:
            await self._session.commit()
        except IntegrityError:
            await self._session.rollback()
            return False
        return True

    async def register_download(self, short_code: str) -> bool:
        """Atomically bump download_count unless the download limit is already reached.

        A single conditional UPDATE keeps the limit exact under concurrent downloads.
        """
        result = await self._session.execute(
            update(FileRecord)
            .where(
                FileRecord.short_code == short_code,
                or_(
                    FileRecord.max_downloads.is_(None),
                    FileRecord.download_count < FileRecord.max_downloads,
                ),
            )
            .values(download_count=FileRecord.download_count + 1)
        )
        await self._session.commit()
        return result.rowcount == 1

    async def list_removable(self, now: datetime) -> list[FileRecord]:
        """Records that are expired or have used up all their downloads."""
        result = await self._session.execute(
            select(FileRecord).where(
                or_(
                    FileRecord.expires_at < now,
                    FileRecord.download_count >= FileRecord.max_downloads,
                )
            )
        )
        return list(result.scalars().all())

    async def delete_many(self, records: list[FileRecord]) -> None:
        for record in records:
            await self._session.delete(record)
        await self._session.commit()

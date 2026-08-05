import asyncio
from datetime import datetime, timezone

from sqlalchemy import select

from app.core.config import UPLOAD_DIR
from app.db.session import AsyncSessionLocal
from app.models.file_record import FileRecord


async def cleanup_expired_files() -> None:
    """
    Delete expired files from disk and database once.
    """
    try:
        async with AsyncSessionLocal() as session:
            now = datetime.now(timezone.utc)
            result = await session.execute(
                select(FileRecord).where(FileRecord.expires_at < now)
            )
            expired = result.scalars().all()

            for rec in expired:
                path = UPLOAD_DIR / rec.stored_name
                if path.exists():
                    path.unlink()
                await session.delete(rec)

            await session.commit()
            print(f"[{datetime.now(timezone.utc).isoformat()}] Cleaned up {len(expired)} expired files.")
    except Exception as e:
        print(f"[{datetime.now(timezone.utc).isoformat()}] Error during cleanup: {e}")

if __name__ == "__main__":
    asyncio.run(cleanup_expired_files())


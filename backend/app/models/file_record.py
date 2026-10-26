import uuid
from datetime import UTC, datetime

from sqlalchemy import BigInteger, DateTime, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from app.db.session import Base


def utcnow() -> datetime:
    return datetime.now(UTC)


def _as_utc(value: datetime) -> datetime:
    """SQLite returns naive datetimes; treat them as UTC so comparisons work."""
    return value if value.tzinfo else value.replace(tzinfo=UTC)


class FileRecord(Base):
    __tablename__ = "files"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    short_code: Mapped[str] = mapped_column(String(8), unique=True)
    original_name: Mapped[str] = mapped_column(String)
    stored_name: Mapped[str] = mapped_column(String)
    file_size: Mapped[int] = mapped_column(BigInteger)
    content_type: Mapped[str] = mapped_column(String)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    expires_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    max_downloads: Mapped[int | None] = mapped_column(Integer, nullable=True)
    download_count: Mapped[int] = mapped_column(Integer, default=0)

    def is_expired(self, now: datetime | None = None) -> bool:
        return self.expires_at is not None and _as_utc(self.expires_at) < (now or utcnow())

    def is_download_limit_reached(self) -> bool:
        return self.max_downloads is not None and self.download_count >= self.max_downloads

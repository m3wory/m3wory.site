import secrets
import string
from collections.abc import Callable
from datetime import timedelta
from pathlib import Path

from fastapi import UploadFile

from app.core.exceptions import (
    DownloadLimitReached,
    FileExpired,
    FileNotFound,
    ShortCodeGenerationError,
)
from app.models.file_record import FileRecord, utcnow
from app.repositories.file_repository import FileRepository
from app.services.storage import LocalFileStorage

SHORT_CODE_ALPHABET = string.ascii_letters + string.digits
SHORT_CODE_LENGTH = 6
MAX_CODE_ATTEMPTS = 10
DEFAULT_FILENAME = "file"


def generate_short_code(length: int = SHORT_CODE_LENGTH) -> str:
    return "".join(secrets.choice(SHORT_CODE_ALPHABET) for _ in range(length))


def sanitize_filename(filename: str | None) -> str:
    """Keep only the base name so user input can never carry a path."""
    name = Path((filename or "").replace("\\", "/")).name.strip()
    if name in {"", ".", ".."}:
        return DEFAULT_FILENAME
    return name[:255]


class FileService:
    """Business rules for uploading, inspecting and downloading shared files."""

    def __init__(
        self,
        repository: FileRepository,
        storage: LocalFileStorage,
        max_file_size_bytes: int,
        code_generator: Callable[[], str] = generate_short_code,
    ) -> None:
        self._repository = repository
        self._storage = storage
        self._max_file_size_bytes = max_file_size_bytes
        self._code_generator = code_generator

    async def upload(
        self, upload: UploadFile, expires_hours: int, max_downloads: int
    ) -> FileRecord:
        stored_name, size = await self._storage.save(upload, self._max_file_size_bytes)

        expires_at = utcnow() + timedelta(hours=expires_hours) if expires_hours > 0 else None
        # The unique constraint on short_code is the source of truth; retry on collision.
        for _ in range(MAX_CODE_ATTEMPTS):
            record = FileRecord(
                short_code=self._code_generator(),
                original_name=sanitize_filename(upload.filename),
                stored_name=stored_name,
                file_size=size,
                content_type=upload.content_type or "application/octet-stream",
                expires_at=expires_at,
                max_downloads=max_downloads if max_downloads > 0 else None,
            )
            if await self._repository.add(record):
                return record

        self._storage.delete(stored_name)
        raise ShortCodeGenerationError

    async def get_info(self, short_code: str) -> FileRecord:
        return await self._get_available(short_code)

    async def open_for_download(self, short_code: str) -> tuple[FileRecord, Path]:
        record = await self._get_available(short_code)
        if not self._storage.exists(record.stored_name):
            raise FileNotFound("File not found on disk")
        if not await self._repository.register_download(short_code):
            raise DownloadLimitReached
        return record, self._storage.path_for(record.stored_name)

    async def _get_available(self, short_code: str) -> FileRecord:
        record = await self._repository.get_by_short_code(short_code)
        if record is None:
            raise FileNotFound
        if record.is_expired():
            raise FileExpired
        if record.is_download_limit_reached():
            raise DownloadLimitReached
        return record

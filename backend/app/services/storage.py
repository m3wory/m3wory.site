import uuid
from pathlib import Path

import aiofiles
from fastapi import UploadFile

from app.core.exceptions import FileTooLarge

CHUNK_SIZE = 1024 * 1024


class LocalFileStorage:
    """Stores uploaded files on local disk under random names."""

    def __init__(self, root: Path) -> None:
        self._root = root
        self._root.mkdir(parents=True, exist_ok=True)

    def path_for(self, stored_name: str) -> Path:
        return self._root / stored_name

    def exists(self, stored_name: str) -> bool:
        return self.path_for(stored_name).exists()

    def delete(self, stored_name: str) -> None:
        self.path_for(stored_name).unlink(missing_ok=True)

    async def save(self, upload: UploadFile, max_bytes: int) -> tuple[str, int]:
        """Stream the upload to disk in chunks. Returns (stored_name, size in bytes).

        Raises FileTooLarge (and removes the partial file) if the upload exceeds max_bytes.
        """
        stored_name = uuid.uuid4().hex
        size = 0
        try:
            async with aiofiles.open(self.path_for(stored_name), "wb") as out:
                while chunk := await upload.read(CHUNK_SIZE):
                    size += len(chunk)
                    if size > max_bytes:
                        raise FileTooLarge(max_bytes)
                    await out.write(chunk)
        except BaseException:
            self.delete(stored_name)
            raise
        return stored_name, size

from __future__ import annotations

from datetime import datetime
from typing import Optional

from pydantic import BaseModel


class UploadResponse(BaseModel):
    short_code: str
    original_name: str
    file_size: int
    expires_at: Optional[datetime] = None
    max_downloads: Optional[int] = None


class FileInfo(BaseModel):
    original_name: str
    file_size: int
    content_type: str
    created_at: datetime
    expires_at: Optional[datetime] = None
    max_downloads: Optional[int] = None
    download_count: int

    class Config:
        from_attributes = True

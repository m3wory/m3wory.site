from datetime import datetime

from pydantic import BaseModel, ConfigDict


class UploadResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    short_code: str
    original_name: str
    file_size: int
    expires_at: datetime | None = None
    max_downloads: int | None = None


class FileInfo(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    original_name: str
    file_size: int
    content_type: str
    created_at: datetime
    expires_at: datetime | None = None
    max_downloads: int | None = None
    download_count: int

import random
import string
import uuid
from datetime import datetime, timedelta, timezone

import aiofiles
from fastapi import APIRouter, File, Form, HTTPException, UploadFile
from fastapi.responses import FileResponse
from sqlalchemy import select

from app.core.config import MAX_FILE_SIZE_MB, UPLOAD_DIR
from app.db.session import AsyncSessionLocal
from app.models.file_record import FileRecord
from app.schemas.file_record import UploadResponse, FileInfo

router = APIRouter(tags=["files"])


def generate_short_code(length: int = 6) -> str:
    chars = string.ascii_letters + string.digits
    return "".join(random.choices(chars, k=length))


@router.post("/upload", response_model=UploadResponse)
async def upload_file(
    file: UploadFile = File(...),
    expires_hours: int = Form(24),
    max_downloads: int = Form(0),
):
    content = await file.read()
    if len(content) > MAX_FILE_SIZE_MB * 1024 * 1024:
        raise HTTPException(
            status_code=400,
            detail=f"File too large. Max size: {MAX_FILE_SIZE_MB} MB",
        )

    stored_name = f"{uuid.uuid4()}_{file.filename}"
    file_path = UPLOAD_DIR / stored_name

    async with aiofiles.open(file_path, "wb") as f:
        await f.write(content)

    async with AsyncSessionLocal() as session:
        code = None
        for _ in range(10):
            code_candidate = generate_short_code()
            existing = await session.execute(
                select(FileRecord).where(FileRecord.short_code == code_candidate)
            )
            if not existing.scalar_one_or_none():
                code = code_candidate
                break

        if not code:
            raise HTTPException(status_code=500, detail="Unable to generate short code")

        expires_at = None
        if expires_hours and expires_hours > 0:
            expires_at = datetime.now(timezone.utc) + timedelta(hours=expires_hours)

        record = FileRecord(
            short_code=code,
            original_name=file.filename,
            stored_name=stored_name,
            file_size=len(content),
            content_type=file.content_type or "application/octet-stream",
            expires_at=expires_at,
            max_downloads=max_downloads if max_downloads > 0 else None,
        )
        session.add(record)
        await session.commit()

    return UploadResponse(
        short_code=code,
        original_name=file.filename,
        file_size=len(content),
        expires_at=expires_at,
        max_downloads=max_downloads if max_downloads > 0 else None,
    )


@router.get("/info/{short_code}", response_model=FileInfo)
async def file_info(short_code: str):
    async with AsyncSessionLocal() as session:
        result = await session.execute(
            select(FileRecord).where(FileRecord.short_code == short_code)
        )
        rec = result.scalar_one_or_none()
        if not rec:
            raise HTTPException(status_code=404, detail="File not found")

        now = datetime.now(timezone.utc)
        if rec.expires_at and rec.expires_at < now:
            raise HTTPException(status_code=410, detail="File has expired")

        if rec.max_downloads and rec.download_count >= rec.max_downloads:
            raise HTTPException(
                status_code=410, detail="Download limit reached"
            )

        return FileInfo(
            original_name=rec.original_name,
            file_size=rec.file_size,
            content_type=rec.content_type,
            created_at=rec.created_at,
            expires_at=rec.expires_at,
            max_downloads=rec.max_downloads,
            download_count=rec.download_count,
        )


@router.get("/download/{short_code}")
async def download_file(short_code: str):
    async with AsyncSessionLocal() as session:
        result = await session.execute(
            select(FileRecord).where(FileRecord.short_code == short_code)
        )
        rec = result.scalar_one_or_none()
        if not rec:
            raise HTTPException(status_code=404, detail="File not found")

        now = datetime.now(timezone.utc)
        if rec.expires_at and rec.expires_at < now:
            raise HTTPException(status_code=410, detail="File has expired")

        if rec.max_downloads and rec.download_count >= rec.max_downloads:
            raise HTTPException(
                status_code=410, detail="Download limit reached"
            )

        file_path = UPLOAD_DIR / rec.stored_name
        if not file_path.exists():
            raise HTTPException(status_code=404, detail="File not found on disk")

        rec.download_count += 1
        await session.commit()

        return FileResponse(
            path=str(file_path),
            filename=rec.original_name,
            media_type=rec.content_type,
        )


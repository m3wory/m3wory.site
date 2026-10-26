from fastapi import APIRouter, Depends, File, Form, UploadFile
from fastapi.responses import FileResponse

from app.api.deps import get_file_service
from app.schemas.file_record import FileInfo, UploadResponse
from app.services.file_service import FileService

router = APIRouter(tags=["files"])


@router.post("/upload", response_model=UploadResponse)
async def upload_file(
    file: UploadFile = File(...),
    expires_hours: int = Form(24),
    max_downloads: int = Form(0),
    service: FileService = Depends(get_file_service),
) -> UploadResponse:
    record = await service.upload(file, expires_hours, max_downloads)
    return UploadResponse.model_validate(record)


@router.get("/info/{short_code}", response_model=FileInfo)
async def file_info(short_code: str, service: FileService = Depends(get_file_service)) -> FileInfo:
    return FileInfo.model_validate(await service.get_info(short_code))


@router.get("/download/{short_code}")
async def download_file(
    short_code: str, service: FileService = Depends(get_file_service)
) -> FileResponse:
    record, path = await service.open_for_download(short_code)
    return FileResponse(path=path, filename=record.original_name, media_type=record.content_type)

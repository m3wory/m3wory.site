from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse

from app.core.exceptions import (
    DownloadLimitReached,
    FileExpired,
    FileNotFound,
    FileServiceError,
    FileTooLarge,
)

STATUS_BY_ERROR: dict[type[FileServiceError], int] = {
    FileNotFound: status.HTTP_404_NOT_FOUND,
    FileExpired: status.HTTP_410_GONE,
    DownloadLimitReached: status.HTTP_410_GONE,
    FileTooLarge: status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
}


async def file_service_error_handler(_: Request, exc: FileServiceError) -> JSONResponse:
    status_code = STATUS_BY_ERROR.get(type(exc), status.HTTP_500_INTERNAL_SERVER_ERROR)
    return JSONResponse(status_code=status_code, content={"detail": exc.detail})


def register_error_handlers(app: FastAPI) -> None:
    app.add_exception_handler(FileServiceError, file_service_error_handler)

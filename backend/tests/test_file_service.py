import io

import pytest
from fastapi import UploadFile

from app.core.exceptions import ShortCodeGenerationError
from app.repositories.file_repository import FileRepository
from app.services.file_service import FileService, generate_short_code, sanitize_filename


@pytest.mark.parametrize(
    ("raw", "expected"),
    [
        ("report.pdf", "report.pdf"),
        ("../../etc/passwd", "passwd"),
        ("C:\\Users\\me\\secret.txt", "secret.txt"),
        ("", "file"),
        (None, "file"),
        ("..", "file"),
    ],
)
def test_sanitize_filename(raw, expected):
    assert sanitize_filename(raw) == expected


def test_generate_short_code_has_expected_shape():
    codes = {generate_short_code() for _ in range(50)}

    assert all(len(code) == 6 and code.isalnum() for code in codes)
    assert len(codes) > 1


def make_upload(content: bytes = b"data", filename: str = "a.txt") -> UploadFile:
    return UploadFile(file=io.BytesIO(content), filename=filename)


def make_service(app, session, code_generator) -> FileService:
    return FileService(
        repository=FileRepository(session),
        storage=app.state.storage,
        max_file_size_bytes=app.state.settings.max_file_size_bytes,
        code_generator=code_generator,
    )


async def test_upload_retries_on_short_code_collision(app):
    codes = iter(["AAAAAA", "AAAAAA", "BBBBBB"])
    # One session per upload, like one request in the real app.
    async with app.state.session_factory() as session:
        first = await make_service(app, session, lambda: next(codes)).upload(
            make_upload(), expires_hours=1, max_downloads=0
        )
    async with app.state.session_factory() as session:
        second = await make_service(app, session, lambda: next(codes)).upload(
            make_upload(), expires_hours=1, max_downloads=0
        )

    assert first.short_code == "AAAAAA"
    assert second.short_code == "BBBBBB"


async def test_upload_fails_and_cleans_disk_when_codes_always_collide(app):
    async with app.state.session_factory() as session:
        service = make_service(app, session, lambda: "AAAAAA")
        await service.upload(make_upload(), expires_hours=1, max_downloads=0)
        files_before = len(list(app.state.settings.upload_dir.iterdir()))

        with pytest.raises(ShortCodeGenerationError):
            await service.upload(make_upload(), expires_hours=1, max_downloads=0)

    assert len(list(app.state.settings.upload_dir.iterdir())) == files_before

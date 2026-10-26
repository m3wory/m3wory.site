class FileServiceError(Exception):
    """Base class for domain errors; the API layer maps them to HTTP responses."""

    default_detail = "File service error"

    def __init__(self, detail: str | None = None) -> None:
        self.detail = detail or self.default_detail
        super().__init__(self.detail)


class FileNotFound(FileServiceError):
    default_detail = "File not found"


class FileExpired(FileServiceError):
    default_detail = "File has expired"


class DownloadLimitReached(FileServiceError):
    default_detail = "Download limit reached"


class FileTooLarge(FileServiceError):
    default_detail = "File too large"

    def __init__(self, max_bytes: int) -> None:
        super().__init__(f"File too large. Max size: {max_bytes // (1024 * 1024)} MB")


class ShortCodeGenerationError(FileServiceError):
    default_detail = "Unable to generate short code"

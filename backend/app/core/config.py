import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

BASE_DIR = Path(__file__).resolve().parent.parent.parent

# Storage
UPLOAD_DIR = Path(os.getenv("UPLOAD_DIR", "/app/uploads"))
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

MAX_FILE_SIZE_MB: int = int(os.getenv("MAX_FILE_SIZE_MB", "100"))

# Database
DATABASE_URL_RAW = os.getenv("DATABASE_URL", "")
DATABASE_URL = DATABASE_URL_RAW.replace("postgresql://", "postgresql+asyncpg://")


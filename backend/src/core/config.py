import os
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parents[2]
STORAGE_DIR = BASE_DIR / "storage" / "files"
STORAGE_DIR.mkdir(parents=True, exist_ok=True)

DATABASE_URL = (
    f"postgresql+asyncpg://{os.environ.get('POSTGRES_USER')}:"
    f"{os.environ.get('POSTGRES_PASSWORD')}@{os.environ.get('POSTGRES_HOST')}:"
    f"{os.environ.get('PGPORT')}/{os.environ.get('POSTGRES_DB')}"
)
REDIS_URL = os.environ.get("REDIS_URL", "redis://backend-redis:6379/0")

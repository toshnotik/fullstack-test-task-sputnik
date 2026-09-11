from pathlib import Path

from src.core import config


def get_stored_path(stored_name: str) -> Path:
    return config.STORAGE_DIR / stored_name


def save_file(stored_name: str, content: bytes) -> Path:
    stored_path = get_stored_path(stored_name)
    stored_path.write_bytes(content)
    return stored_path


def file_exists(stored_name: str) -> bool:
    return get_stored_path(stored_name).exists()


def delete_file(stored_name: str) -> None:
    stored_path = get_stored_path(stored_name)
    if stored_path.exists():
        stored_path.unlink()


def read_text(stored_name: str) -> str:
    return get_stored_path(stored_name).read_text(encoding="utf-8", errors="ignore")


def read_bytes(stored_name: str) -> bytes:
    return get_stored_path(stored_name).read_bytes()

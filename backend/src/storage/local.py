import asyncio
from collections.abc import Awaitable
from contextlib import suppress
from pathlib import Path
from typing import BinaryIO, Protocol

from src.core import config

UPLOAD_CHUNK_SIZE = 1024 * 1024


class UploadReader(Protocol):
    @property
    def filename(self) -> str | None: ...

    @property
    def content_type(self) -> str | None: ...

    def read(self, size: int = -1) -> Awaitable[bytes]: ...


def get_stored_path(stored_name: str) -> Path:
    return config.STORAGE_DIR / stored_name


async def save_upload_file(
    stored_name: str,
    upload_file: UploadReader,
    chunk_size: int = UPLOAD_CHUNK_SIZE,
) -> int:
    stored_path = get_stored_path(stored_name)
    total_size = 0

    try:
        target = await asyncio.to_thread(stored_path.open, "wb")
        try:
            while True:
                chunk = await upload_file.read(chunk_size)
                if not chunk:
                    break
                total_size += len(chunk)
                await asyncio.to_thread(_write_chunk, target, chunk)
        finally:
            await asyncio.to_thread(target.close)
    except Exception:
        with suppress(Exception):
            delete_file(stored_name)
        raise

    return total_size


def _write_chunk(target: BinaryIO, chunk: bytes) -> None:
    target.write(chunk)


def file_exists(stored_name: str) -> bool:
    return get_stored_path(stored_name).exists()


def delete_file(stored_name: str) -> None:
    stored_path = get_stored_path(stored_name)
    try:
        stored_path.unlink()
    except FileNotFoundError:
        pass


def read_text(stored_name: str) -> str:
    return get_stored_path(stored_name).read_text(encoding="utf-8", errors="ignore")


def read_bytes(stored_name: str) -> bytes:
    return get_stored_path(stored_name).read_bytes()

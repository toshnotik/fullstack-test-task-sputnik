import mimetypes
from pathlib import Path
from typing import Any
from uuid import uuid4

from src.core import database
from src.exceptions import EmptyFileError, StoredFileContentNotFound, StoredFileNotFound
from src.models import StoredFile
from src.repositories import files as files_repository
from src.storage import local as local_storage


async def list_files() -> list[StoredFile]:
    async with database.async_session_maker() as session:
        return await files_repository.list_files(session)


async def get_file(file_id: str) -> StoredFile:
    async with database.async_session_maker() as session:
        file_item = await files_repository.get_file(session, file_id)
        if not file_item:
            raise StoredFileNotFound
        return file_item


async def create_file(title: str, upload_file: Any) -> StoredFile:
    content = await upload_file.read()
    if not content:
        raise EmptyFileError

    file_id = str(uuid4())
    suffix = Path(upload_file.filename or "").suffix
    stored_name = f"{file_id}{suffix}"
    local_storage.save_file(stored_name, content)

    file_item = StoredFile(
        id=file_id,
        title=title,
        original_name=upload_file.filename or stored_name,
        stored_name=stored_name,
        mime_type=upload_file.content_type or mimetypes.guess_type(stored_name)[0] or "application/octet-stream",
        size=len(content),
        processing_status="uploaded",
    )
    async with database.async_session_maker() as session:
        files_repository.add_file(session, file_item)
        await session.commit()
        await files_repository.refresh_file(session, file_item)
    return file_item


async def update_file(file_id: str, title: str) -> StoredFile:
    async with database.async_session_maker() as session:
        file_item = await files_repository.get_file(session, file_id)
        if not file_item:
            raise StoredFileNotFound
        files_repository.update_file_title(file_item, title)
        await session.commit()
        await files_repository.refresh_file(session, file_item)
        return file_item


async def delete_file(file_id: str) -> None:
    async with database.async_session_maker() as session:
        file_item = await files_repository.get_file(session, file_id)
        if not file_item:
            raise StoredFileNotFound
        local_storage.delete_file(file_item.stored_name)
        await files_repository.delete_file(session, file_item)
        await session.commit()


async def get_file_path(file_id: str) -> tuple[StoredFile, Path]:
    file_item = await get_file(file_id)
    if not local_storage.file_exists(file_item.stored_name):
        raise StoredFileContentNotFound
    return file_item, local_storage.get_stored_path(file_item.stored_name)

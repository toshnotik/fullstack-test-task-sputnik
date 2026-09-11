from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.models import StoredFile


async def list_files(session: AsyncSession) -> list[StoredFile]:
    result = await session.execute(select(StoredFile).order_by(StoredFile.created_at.desc()))
    return list(result.scalars().all())


async def get_file(session: AsyncSession, file_id: str) -> StoredFile | None:
    return await session.get(StoredFile, file_id)


def add_file(session: AsyncSession, file_item: StoredFile) -> None:
    session.add(file_item)


def update_file_title(file_item: StoredFile, title: str) -> None:
    file_item.title = title


async def delete_file(session: AsyncSession, file_item: StoredFile) -> None:
    await session.delete(file_item)


async def refresh_file(session: AsyncSession, file_item: StoredFile) -> None:
    await session.refresh(file_item)

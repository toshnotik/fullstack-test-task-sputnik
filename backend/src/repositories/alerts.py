from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.models import Alert


async def list_alerts(session: AsyncSession) -> list[Alert]:
    result = await session.execute(select(Alert).order_by(Alert.created_at.desc()))
    return list(result.scalars().all())


def create_alert(file_id: str, level: str, message: str) -> Alert:
    return Alert(file_id=file_id, level=level, message=message)


def add_alert(session: AsyncSession, alert: Alert) -> None:
    session.add(alert)


async def refresh_alert(session: AsyncSession, alert: Alert) -> None:
    await session.refresh(alert)


async def delete_alerts_for_file(session: AsyncSession, file_id: str) -> None:
    await session.execute(delete(Alert).where(Alert.file_id == file_id))

from sqlalchemy import select

from src.core import database
from src.models import Alert


async def list_alerts() -> list[Alert]:
    async with database.async_session_maker() as session:
        result = await session.execute(select(Alert).order_by(Alert.created_at.desc()))
        return list(result.scalars().all())


async def create_alert(file_id: str, level: str, message: str) -> Alert:
    alert = Alert(file_id=file_id, level=level, message=message)
    async with database.async_session_maker() as session:
        session.add(alert)
        await session.commit()
        await session.refresh(alert)
        return alert

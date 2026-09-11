from src.core import database
from src.models import Alert
from src.repositories import alerts as alerts_repository


async def list_alerts() -> list[Alert]:
    async with database.async_session_maker() as session:
        return await alerts_repository.list_alerts(session)


async def create_alert(file_id: str, level: str, message: str) -> Alert:
    alert = alerts_repository.create_alert(file_id=file_id, level=level, message=message)
    async with database.async_session_maker() as session:
        alerts_repository.add_alert(session, alert)
        await session.commit()
        await alerts_repository.refresh_alert(session, alert)
        return alert

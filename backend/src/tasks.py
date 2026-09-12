import asyncio
from collections.abc import Awaitable
from typing import TypeVar

from celery import Celery

from src.core import config, database
from src.services import processing

celery_app = Celery("file_tasks", broker=config.REDIS_URL, backend=config.REDIS_URL)

T = TypeVar("T")


async def run_processing(coroutine: Awaitable[T]) -> T:
    try:
        return await coroutine
    finally:
        await database.engine.dispose()


@celery_app.task
def scan_file_for_threats(file_id: str) -> None:
    if asyncio.run(run_processing(processing.scan_file_for_threats(file_id))):
        extract_file_metadata.delay(file_id)


@celery_app.task
def extract_file_metadata(file_id: str) -> None:
    if asyncio.run(run_processing(processing.extract_file_metadata(file_id))):
        send_file_alert.delay(file_id)


@celery_app.task
def send_file_alert(file_id: str) -> None:
    asyncio.run(run_processing(processing.create_file_alert(file_id)))

from pathlib import Path
from typing import Any

import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import async_sessionmaker

from src.models import Alert, StoredFile
from src.services import processing
from src.storage import local as local_storage


async def create_stored_file(
    session_maker: async_sessionmaker[Any],
    *,
    file_id: str = "processing-file",
    original_name: str = "document.txt",
    stored_name: str = "processing-file.txt",
    mime_type: str = "text/plain",
    size: int = 12,
    processing_status: str = "uploaded",
    scan_status: str | None = None,
    scan_details: str | None = None,
    requires_attention: bool = False,
) -> StoredFile:
    file_item = StoredFile(
        id=file_id,
        title="Processing file",
        original_name=original_name,
        stored_name=stored_name,
        mime_type=mime_type,
        size=size,
        processing_status=processing_status,
        scan_status=scan_status,
        scan_details=scan_details,
        requires_attention=requires_attention,
    )
    async with session_maker() as session:
        session.add(file_item)
        await session.commit()
    return file_item


@pytest.mark.asyncio
async def test_scan_file_for_threats_marks_clean_file(
    test_context: tuple[async_sessionmaker[Any], Path],
) -> None:
    session_maker, _ = test_context
    await create_stored_file(session_maker)

    result = await processing.scan_file_for_threats("processing-file")

    assert result is True
    async with session_maker() as session:
        file_item = await session.get(StoredFile, "processing-file")

    assert file_item is not None
    assert file_item.processing_status == "processing"
    assert file_item.scan_status == "clean"
    assert file_item.scan_details == "no threats found"
    assert file_item.requires_attention is False


@pytest.mark.asyncio
async def test_scan_file_for_threats_marks_suspicious_file(
    test_context: tuple[async_sessionmaker[Any], Path],
) -> None:
    session_maker, _ = test_context
    await create_stored_file(
        session_maker,
        original_name="payload.exe",
        stored_name="processing-file.exe",
    )

    result = await processing.scan_file_for_threats("processing-file")

    assert result is True
    async with session_maker() as session:
        file_item = await session.get(StoredFile, "processing-file")

    assert file_item is not None
    assert file_item.processing_status == "processing"
    assert file_item.scan_status == "suspicious"
    assert file_item.scan_details == "suspicious extension .exe"
    assert file_item.requires_attention is True


@pytest.mark.asyncio
async def test_extract_file_metadata_records_text_metadata(
    test_context: tuple[async_sessionmaker[Any], Path],
) -> None:
    session_maker, _ = test_context
    await create_stored_file(session_maker, size=11)
    local_storage.get_stored_path("processing-file.txt").write_text("hello\nworld", encoding="utf-8")

    result = await processing.extract_file_metadata("processing-file")

    assert result is True
    async with session_maker() as session:
        file_item = await session.get(StoredFile, "processing-file")

    assert file_item is not None
    assert file_item.processing_status == "processed"
    assert file_item.metadata_json == {
        "extension": ".txt",
        "size_bytes": 11,
        "mime_type": "text/plain",
        "line_count": 2,
        "char_count": 11,
    }


@pytest.mark.asyncio
async def test_extract_file_metadata_marks_missing_storage_as_failed(
    test_context: tuple[async_sessionmaker[Any], Path],
) -> None:
    session_maker, _ = test_context
    await create_stored_file(session_maker, scan_status=None)

    result = await processing.extract_file_metadata("processing-file")

    assert result is True
    async with session_maker() as session:
        file_item = await session.get(StoredFile, "processing-file")

    assert file_item is not None
    assert file_item.processing_status == "failed"
    assert file_item.scan_status == "failed"
    assert file_item.scan_details == "stored file not found during metadata extraction"


@pytest.mark.parametrize(
    ("processing_status", "scan_status", "scan_details", "requires_attention", "expected_level", "expected_message"),
    [
        ("processed", "clean", "no threats found", False, "info", "File processed successfully"),
        (
            "processed",
            "suspicious",
            "suspicious extension .exe",
            True,
            "warning",
            "File requires attention: suspicious extension .exe",
        ),
        ("failed", "failed", "stored file not found during metadata extraction", False, "critical", "File processing failed"),
    ],
)
@pytest.mark.asyncio
async def test_create_file_alert_uses_current_file_state(
    test_context: tuple[async_sessionmaker[Any], Path],
    processing_status: str,
    scan_status: str,
    scan_details: str,
    requires_attention: bool,
    expected_level: str,
    expected_message: str,
) -> None:
    session_maker, _ = test_context
    await create_stored_file(
        session_maker,
        processing_status=processing_status,
        scan_status=scan_status,
        scan_details=scan_details,
        requires_attention=requires_attention,
    )

    result = await processing.create_file_alert("processing-file")

    assert result is True
    async with session_maker() as session:
        alerts = await session.execute(select(Alert).where(Alert.file_id == "processing-file"))

    alert = alerts.scalar_one()
    assert alert.level == expected_level
    assert alert.message == expected_message


@pytest.mark.asyncio
async def test_processing_steps_ignore_missing_stored_file(
    test_context: tuple[async_sessionmaker[Any], Path],
) -> None:
    session_maker, _ = test_context

    assert await processing.scan_file_for_threats("missing") is False
    assert await processing.extract_file_metadata("missing") is False
    assert await processing.create_file_alert("missing") is False

    async with session_maker() as session:
        alerts = await session.execute(select(Alert))

    assert list(alerts.scalars()) == []

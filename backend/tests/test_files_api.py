from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any

import pytest
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import async_sessionmaker

from src.api import files as files_api
from src.models import Alert, StoredFile


class DelaySpy:
    def __init__(self) -> None:
        self.calls: list[str] = []

    def delay(self, file_id: str) -> None:
        self.calls.append(file_id)


@pytest.fixture
def scan_spy(monkeypatch: pytest.MonkeyPatch) -> DelaySpy:
    spy = DelaySpy()
    monkeypatch.setattr(files_api, "scan_file_for_threats", spy)
    return spy


async def upload_file(
    client: AsyncClient,
    *,
    title: str = "Document",
    filename: str = "document.txt",
    content: bytes = b"hello",
    content_type: str = "text/plain",
) -> dict[str, Any]:
    response = await client.post(
        "/files",
        data={"title": title},
        files={"file": (filename, content, content_type)},
    )
    assert response.status_code == 201
    return response.json()


@pytest.mark.asyncio
async def test_upload_file_persists_metadata_and_stored_file(
    client: AsyncClient,
    scan_spy: DelaySpy,
    test_context: tuple[async_sessionmaker[Any], Path],
) -> None:
    _, storage_dir = test_context

    body = await upload_file(
        client,
        title="Quarterly report",
        filename="report.txt",
        content=b"hello\nworld",
        content_type="text/plain",
    )

    assert body["title"] == "Quarterly report"
    assert body["original_name"] == "report.txt"
    assert body["mime_type"] == "text/plain"
    assert body["size"] == 11
    assert body["processing_status"] == "uploaded"
    assert body["scan_status"] is None
    assert body["scan_details"] is None
    assert body["metadata_json"] is None
    assert body["requires_attention"] is False
    assert body["created_at"]
    assert body["updated_at"]

    assert scan_spy.calls == [body["id"]]
    stored_path = storage_dir / f"{body['id']}.txt"
    assert stored_path.read_bytes() == b"hello\nworld"


@pytest.mark.asyncio
async def test_list_files_returns_uploaded_files(
    client: AsyncClient,
    scan_spy: DelaySpy,
) -> None:
    first = await upload_file(client, title="First", filename="first.txt")
    second = await upload_file(client, title="Second", filename="second.txt")

    response = await client.get("/files")

    assert response.status_code == 200
    assert {item["id"] for item in response.json()} == {first["id"], second["id"]}
    assert scan_spy.calls == [first["id"], second["id"]]


@pytest.mark.asyncio
async def test_get_one_file_returns_file_metadata(
    client: AsyncClient,
    scan_spy: DelaySpy,
) -> None:
    uploaded = await upload_file(client, title="Find me", filename="find-me.txt")

    response = await client.get(f"/files/{uploaded['id']}")

    assert response.status_code == 200
    assert response.json()["id"] == uploaded["id"]
    assert response.json()["title"] == "Find me"
    assert response.json()["original_name"] == "find-me.txt"


@pytest.mark.asyncio
async def test_download_file_returns_stored_content_and_headers(
    client: AsyncClient,
    scan_spy: DelaySpy,
) -> None:
    uploaded = await upload_file(
        client,
        filename="download-me.txt",
        content=b"download me",
        content_type="text/plain",
    )

    response = await client.get(f"/files/{uploaded['id']}/download")

    assert response.status_code == 200
    assert response.content == b"download me"
    assert response.headers["content-type"].startswith("text/plain")
    assert 'filename="download-me.txt"' in response.headers["content-disposition"]


@pytest.mark.asyncio
async def test_update_file_name_changes_title_only(
    client: AsyncClient,
    scan_spy: DelaySpy,
) -> None:
    uploaded = await upload_file(client, title="Old name", filename="same-file.txt")

    response = await client.patch(f"/files/{uploaded['id']}", json={"title": "New name"})

    assert response.status_code == 200
    body = response.json()
    assert body["title"] == "New name"
    assert body["original_name"] == "same-file.txt"


@pytest.mark.asyncio
async def test_delete_file_removes_database_row_and_stored_file(
    client: AsyncClient,
    scan_spy: DelaySpy,
    test_context: tuple[async_sessionmaker[Any], Path],
) -> None:
    session_maker, storage_dir = test_context
    uploaded = await upload_file(client, filename="delete-me.txt", content=b"delete me")

    response = await client.delete(f"/files/{uploaded['id']}")

    assert response.status_code == 204
    assert response.content == b""
    assert not (storage_dir / f"{uploaded['id']}.txt").exists()

    async with session_maker() as session:
        file_item = await session.get(StoredFile, uploaded["id"])

    assert file_item is None


@pytest.mark.asyncio
async def test_list_alerts_returns_alerts_newest_first(
    client: AsyncClient,
    test_context: tuple[async_sessionmaker[Any], Path],
) -> None:
    session_maker, _ = test_context
    async with session_maker() as session:
        session.add(
            StoredFile(
                id="file-with-alerts",
                title="File with alerts",
                original_name="alerts.txt",
                stored_name="alerts.txt",
                mime_type="text/plain",
                size=5,
                processing_status="processed",
            )
        )
        await session.commit()
        session.add_all(
            [
                Alert(
                    file_id="file-with-alerts",
                    level="info",
                    message="older",
                    created_at=datetime(2026, 1, 1, tzinfo=UTC),
                ),
                Alert(
                    file_id="file-with-alerts",
                    level="warning",
                    message="newer",
                    created_at=datetime(2026, 1, 1, tzinfo=UTC) + timedelta(seconds=1),
                ),
            ]
        )
        await session.commit()

    response = await client.get("/alerts")

    assert response.status_code == 200
    assert [item["message"] for item in response.json()] == ["newer", "older"]
    assert [item["level"] for item in response.json()] == ["warning", "info"]


@pytest.mark.asyncio
async def test_missing_file_operations_return_404(client: AsyncClient) -> None:
    missing_id = "00000000-0000-0000-0000-000000000000"

    get_response = await client.get(f"/files/{missing_id}")
    update_response = await client.patch(f"/files/{missing_id}", json={"title": "Nope"})
    delete_response = await client.delete(f"/files/{missing_id}")
    download_response = await client.get(f"/files/{missing_id}/download")

    assert get_response.status_code == 404
    assert get_response.json() == {"detail": "File not found"}
    assert update_response.status_code == 404
    assert update_response.json() == {"detail": "File not found"}
    assert delete_response.status_code == 404
    assert delete_response.json() == {"detail": "File not found"}
    assert download_response.status_code == 404
    assert download_response.json() == {"detail": "File not found"}


@pytest.mark.asyncio
async def test_delete_file_referenced_by_alert_returns_500_and_leaves_orphaned_storage_state(
    client: AsyncClient,
    scan_spy: DelaySpy,
    test_context: tuple[async_sessionmaker[Any], Path],
) -> None:
    session_maker, storage_dir = test_context
    uploaded = await upload_file(client, filename="referenced.txt", content=b"referenced")
    stored_path = storage_dir / f"{uploaded['id']}.txt"
    async with session_maker() as session:
        session.add(Alert(file_id=uploaded["id"], level="warning", message="still references file"))
        await session.commit()

    response = await client.delete(f"/files/{uploaded['id']}")

    assert response.status_code == 500
    assert response.text == "Internal Server Error"
    assert not stored_path.exists()

    async with session_maker() as session:
        file_item = await session.get(StoredFile, uploaded["id"])
        alerts = await session.execute(select(Alert).where(Alert.file_id == uploaded["id"]))

    assert file_item is not None
    assert len(list(alerts.scalars())) == 1

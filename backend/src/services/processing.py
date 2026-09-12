from pathlib import Path

from src.core import database
from src.repositories import alerts as alerts_repository
from src.repositories import files as files_repository
from src.storage import local as local_storage


async def scan_file_for_threats(file_id: str) -> bool:
    async with database.async_session_maker() as session:
        file_item = await files_repository.get_file(session, file_id)
        if not file_item:
            return False

        file_item.processing_status = "processing"
        reasons: list[str] = []
        extension = Path(file_item.original_name).suffix.lower()

        if extension in {".exe", ".bat", ".cmd", ".sh", ".js"}:
            reasons.append(f"suspicious extension {extension}")

        if file_item.size > 10 * 1024 * 1024:
            reasons.append("file is larger than 10 MB")

        if extension == ".pdf" and file_item.mime_type not in {
            "application/pdf",
            "application/octet-stream",
        }:
            reasons.append("pdf extension does not match mime type")

        file_item.scan_status = "suspicious" if reasons else "clean"
        file_item.scan_details = ", ".join(reasons) if reasons else "no threats found"
        file_item.requires_attention = bool(reasons)
        await session.commit()

    return True


async def extract_file_metadata(file_id: str) -> bool:
    async with database.async_session_maker() as session:
        file_item = await files_repository.get_file(session, file_id)
        if not file_item:
            return False

        if not local_storage.file_exists(file_item.stored_name):
            file_item.processing_status = "failed"
            file_item.scan_status = file_item.scan_status or "failed"
            file_item.scan_details = "stored file not found during metadata extraction"
            await session.commit()
            return True

        metadata = {
            "extension": Path(file_item.original_name).suffix.lower(),
            "size_bytes": file_item.size,
            "mime_type": file_item.mime_type,
        }

        if file_item.mime_type.startswith("text/"):
            text_content = local_storage.read_text(file_item.stored_name)
            metadata["line_count"] = len(text_content.splitlines())
            metadata["char_count"] = len(text_content)
        elif file_item.mime_type == "application/pdf":
            pdf_content = local_storage.read_bytes(file_item.stored_name)
            metadata["approx_page_count"] = max(pdf_content.count(b"/Type /Page"), 1)

        file_item.metadata_json = metadata
        file_item.processing_status = "processed"
        await session.commit()

    return True


async def create_file_alert(file_id: str) -> bool:
    async with database.async_session_maker() as session:
        file_item = await files_repository.get_file(session, file_id)
        if not file_item:
            return False

        if file_item.processing_status == "failed":
            alert = alerts_repository.create_alert(
                file_id=file_id,
                level="critical",
                message="File processing failed",
            )
        elif file_item.requires_attention:
            alert = alerts_repository.create_alert(
                file_id=file_id,
                level="warning",
                message=f"File requires attention: {file_item.scan_details}",
            )
        else:
            alert = alerts_repository.create_alert(
                file_id=file_id,
                level="info",
                message="File processed successfully",
            )

        alerts_repository.add_alert(session, alert)
        await session.commit()

    return True

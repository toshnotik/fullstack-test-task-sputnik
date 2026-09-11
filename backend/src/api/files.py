from fastapi import APIRouter, File, Form, HTTPException, UploadFile
from fastapi.responses import FileResponse
from starlette import status

from src.exceptions import EmptyFileError, StoredFileContentNotFound, StoredFileNotFound
from src.schemas import FileItem, FileUpdate
from src.services.files import create_file, delete_file, get_file, get_file_path, list_files, update_file
from src.tasks import scan_file_for_threats


router = APIRouter()


def file_not_found_response() -> HTTPException:
    return HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="File not found")


@router.get("/files", response_model=list[FileItem])
async def list_files_view():
    return await list_files()


@router.post("/files", response_model=FileItem, status_code=201)
async def create_file_view(
    title: str = Form(...),
    file: UploadFile = File(...),
):
    try:
        file_item = await create_file(title=title, upload_file=file)
    except EmptyFileError as error:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="File is empty") from error
    scan_file_for_threats.delay(file_item.id)
    return file_item


@router.get("/files/{file_id}", response_model=FileItem)
async def get_file_view(file_id: str):
    try:
        return await get_file(file_id)
    except StoredFileNotFound as error:
        raise file_not_found_response() from error


@router.patch("/files/{file_id}", response_model=FileItem)
async def update_file_view(
    file_id: str,
    payload: FileUpdate,
):
    try:
        return await update_file(file_id=file_id, title=payload.title)
    except StoredFileNotFound as error:
        raise file_not_found_response() from error


@router.get("/files/{file_id}/download")
async def download_file(file_id: str):
    try:
        file_item, stored_path = await get_file_path(file_id)
    except StoredFileNotFound as error:
        raise file_not_found_response() from error
    except StoredFileContentNotFound as error:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Stored file not found") from error
    return FileResponse(
        path=stored_path,
        media_type=file_item.mime_type,
        filename=file_item.original_name,
    )


@router.delete("/files/{file_id}", status_code=204)
async def delete_file_view(file_id: str):
    try:
        await delete_file(file_id)
    except StoredFileNotFound as error:
        raise file_not_found_response() from error

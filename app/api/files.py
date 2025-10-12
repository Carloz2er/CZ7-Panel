from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File
from fastapi.responses import StreamingResponse
from typing import List
import io

from app.api.deps import get_db, get_current_user
from app.models.user_model import User
from app.models.service import Service
from app.schemas.file import FileItem
from app.core import file_manager

router = APIRouter()

def get_service_for_user(service_id: int, db = Depends(get_db), user: User = Depends(get_current_user)) -> Service:
    service = db.query(Service).filter(Service.id == service_id, Service.owner_id == user.id).first()
    if not service:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Service not found or you do not have permission to access it.")
    return service

@router.get("/{service_id}/files", response_model=List[FileItem])
def list_service_files(
    service: Service = Depends(get_service_for_user),
    path: str = "/"
):
    """
    List files and directories for a service.
    """
    try:
        return file_manager.list_files(service.id, path)
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

@router.get("/{service_id}/files/download", response_class=StreamingResponse)
def download_service_file(
    service: Service = Depends(get_service_for_user),
    path: str = "/"
):
    """
    Download a file from a service.
    """
    try:
        file_bytes = file_manager.read_file(service.id, path)
        return StreamingResponse(io.BytesIO(file_bytes), media_type="application/octet-stream")
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

@router.post("/{service_id}/files/upload")
async def upload_service_file(
    service: Service = Depends(get_service_for_user),
    path: str = "/",
    file: UploadFile = File(...)
):
    """
    Upload a file to a service's directory.
    """
    try:
        contents = await file.read()
        file_manager.write_file(service.id, f"{path}/{file.filename}", contents)
        return {"filename": file.filename, "path": path}
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))

@router.delete("/{service_id}/files")
def delete_service_file(
    service: Service = Depends(get_service_for_user),
    path: str = "/"
):
    """
    Delete a file or directory in a service.
    """
    try:
        file_manager.delete_file(service.id, path)
        return {"status": "success", "detail": f"Deleted {path}"}
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
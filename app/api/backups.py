from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from typing import List

from app.api.deps import get_db, get_current_user
from app.models.user_model import User
from app.models.service import Service
from app.models.backup import Backup
from app.schemas.backup import Backup as BackupSchema
from app.core import backup_manager

router = APIRouter()

@router.get("/services/{service_id}/backups", response_model=List[BackupSchema])
def list_backups_for_service(
    service_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    service = db.query(Service).filter(Service.id == service_id, Service.owner_id == current_user.id).first()
    if not service:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Service not found")

    return db.query(Backup).filter(Backup.service_id == service_id).all()

@router.post("/services/{service_id}/backups", response_model=BackupSchema, status_code=status.HTTP_201_CREATED)
def create_service_backup(
    service_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    service = db.query(Service).filter(Service.id == service_id, Service.owner_id == current_user.id).first()
    if not service:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Service not found")

    try:
        filename, size_bytes = backup_manager.create_backup(service.id)

        new_backup = Backup(
            service_id=service.id,
            filename=filename,
            size_bytes=size_bytes
        )
        db.add(new_backup)
        db.commit()
        db.refresh(new_backup)
        return new_backup
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Failed to create backup: {e}")

@router.get("/backups/{backup_id}/download", response_class=FileResponse)
def download_backup(
    backup_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    backup = db.query(Backup).filter(Backup.id == backup_id).first()
    if not backup:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Backup not found")

    service = db.query(Service).filter(Service.id == backup.service_id, Service.owner_id == current_user.id).first()
    if not service:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not enough permissions")

    backup_path = backup_manager.get_backup_path(backup.service_id, backup.filename)
    return FileResponse(path=backup_path, filename=backup.filename, media_type='application/gzip')

@router.post("/backups/{backup_id}/restore", status_code=status.HTTP_200_OK)
def restore_service_from_backup(
    backup_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    backup = db.query(Backup).filter(Backup.id == backup_id).first()
    if not backup:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Backup not found")

    service = db.query(Service).filter(Service.id == backup.service_id, Service.owner_id == current_user.id).first()
    if not service:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not enough permissions")

    try:
        backup_manager.restore_from_backup(backup.service_id, backup.filename)
        return {"status": "success", "detail": f"Service {service.id} restored from backup {backup.id}"}
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Failed to restore backup: {e}")

@router.delete("/backups/{backup_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_backup(
    backup_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    backup = db.query(Backup).filter(Backup.id == backup_id).first()
    if not backup:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Backup not found")

    service = db.query(Service).filter(Service.id == backup.service_id, Service.owner_id == current_user.id).first()
    if not service:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not enough permissions")

    try:
        backup_manager.delete_backup_file(backup.service_id, backup.filename)
        db.delete(backup)
        db.commit()
        return
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Failed to delete backup: {e}")
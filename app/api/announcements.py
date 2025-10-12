import uuid
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List

from app.api.deps import get_db, get_current_active_superuser
from app.models.announcement import Announcement
from app.schemas.announcement import Announcement as AnnouncementSchema, AnnouncementCreate, AnnouncementUpdate

router = APIRouter()

@router.get("/", response_model=List[AnnouncementSchema])
def list_active_announcements(db: Session = Depends(get_db)):
    """
    List all active announcements.
    """
    announcements = db.query(Announcement).filter(Announcement.is_active == True).all()
    return announcements

@router.post("/", response_model=AnnouncementSchema, status_code=status.HTTP_201_CREATED, dependencies=[Depends(get_current_active_superuser)])
def create_announcement(
    *,
    db: Session = Depends(get_db),
    announcement_in: AnnouncementCreate
):
    """
    Create a new announcement (Superuser only).
    """
    new_announcement = Announcement(
        id=str(uuid.uuid4()),
        content=announcement_in.content,
        is_active=announcement_in.is_active
    )
    db.add(new_announcement)
    db.commit()
    db.refresh(new_announcement)
    return new_announcement

@router.put("/{announcement_id}", response_model=AnnouncementSchema, dependencies=[Depends(get_current_active_superuser)])
def update_announcement(
    announcement_id: str,
    *,
    db: Session = Depends(get_db),
    announcement_in: AnnouncementUpdate
):
    """
    Update an announcement (Superuser only).
    """
    announcement = db.query(Announcement).filter(Announcement.id == announcement_id).first()
    if not announcement:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Announcement not found")

    update_data = announcement_in.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(announcement, field, value)

    db.add(announcement)
    db.commit()
    db.refresh(announcement)
    return announcement

@router.delete("/{announcement_id}", status_code=status.HTTP_204_NO_CONTENT, dependencies=[Depends(get_current_active_superuser)])
def delete_announcement(
    announcement_id: str,
    *,
    db: Session = Depends(get_db)
):
    """
    Delete an announcement (Superuser only).
    """
    announcement = db.query(Announcement).filter(Announcement.id == announcement_id).first()
    if not announcement:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Announcement not found")

    db.delete(announcement)
    db.commit()
    return
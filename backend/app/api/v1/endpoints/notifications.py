import uuid
from typing import Any, List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.api.v1.endpoints.deps import get_current_user, get_db
from app.models.user import User
from app.schemas.realtime import (
    NotificationListResponse,
    NotificationMarkReadRequest,
    NotificationResponse,
)
from app.services.notification import NotificationService

router = APIRouter()


@router.get("", response_model=NotificationListResponse)
def list_notifications(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    unread_only: bool = Query(False),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Any:
    """List notifications for current user with tenant isolation and role targeting."""
    items, total, unread_count = NotificationService.list_notifications(
        db=db,
        user=current_user,
        skip=skip,
        limit=limit,
        unread_only=unread_only,
    )
    return {
        "items": items,
        "total": total,
        "unread_count": unread_count,
    }


@router.post("/{notification_id}/read", response_model=dict)
def mark_notification_read(
    notification_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Any:
    """Mark a single notification as read."""
    count = NotificationService.mark_as_read(db, current_user, [notification_id])
    if count == 0:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Notification not found or access denied",
        )
    return {"status": "success", "updated": count}


@router.post("/read-all", response_model=dict)
def mark_all_notifications_read(
    req: Optional[NotificationMarkReadRequest] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Any:
    """Mark all unread notifications as read for current user."""
    notification_ids = req.notification_ids if req else None
    count = NotificationService.mark_as_read(db, current_user, notification_ids)
    return {"status": "success", "updated": count}

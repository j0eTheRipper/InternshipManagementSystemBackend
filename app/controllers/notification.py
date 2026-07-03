from typing import Annotated

from fastapi import APIRouter, Depends

from app.dependencies.auth import get_current_user
from app.models.Notification import Notification
from app.models.User import User

router = APIRouter(prefix="/notifications")


@router.get("/")
async def get_notifications(user: Annotated[User, Depends(get_current_user)]):
    return Notification.get_notifications(user.user_id)


@router.get("/unread-count")
async def get_unread_count(user: Annotated[User, Depends(get_current_user)]):
    count = Notification.get_unread_count(user.user_id)
    return {"unread_count": count}


@router.patch("/{notification_id}/read")
async def mark_as_read(
    notification_id: int,
    user: Annotated[User, Depends(get_current_user)],
):
    Notification.mark_as_read(notification_id)
    return {"message": "Notification marked as read"}

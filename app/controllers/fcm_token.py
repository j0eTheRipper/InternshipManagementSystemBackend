from typing import Annotated

from fastapi import APIRouter, Depends
from pydantic import BaseModel

from app.dependencies.auth import get_current_user
from app.models.FcmToken import FcmToken
from app.models.User import User

router = APIRouter(prefix="/fcm-token")


class FcmTokenRequest(BaseModel):
    token: str


@router.post("")
async def save_token(
    body: FcmTokenRequest,
    user: Annotated[User, Depends(get_current_user)],
):
    FcmToken.save(user.user_id, body.token)
    return {"message": "FCM token saved"}


@router.delete("")
async def delete_token(
    body: FcmTokenRequest,
    user: Annotated[User, Depends(get_current_user)],
):
    FcmToken.delete(body.token)
    return {"message": "FCM token deleted"}

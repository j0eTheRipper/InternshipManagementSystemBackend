from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException

from app.dependencies.auth import get_current_user
from app.models.Requests.UpdateProfileRequest import UpdateProfileRequest
from app.models.User import User

router = APIRouter()


@router.patch("/profile")
async def update_profile(
    body: UpdateProfileRequest,
    user: Annotated[User, Depends(get_current_user)],
):
    if not User.verify_password(user.user_id, body.current_password):
        raise HTTPException(403, "Incorrect password")

    if body.new_email is not None:
        existing = User.get_by_email(body.new_email)
        if existing is not None and existing.user_id != user.user_id:
            raise HTTPException(409, "Email already in use")
        User.update_email(user.user_id, body.new_email)

    if body.new_password is not None:
        User.update_password(user.user_id, body.new_password)

    updated_user = User.getUserData(user.user_id)
    return updated_user.model_dump(mode="json")

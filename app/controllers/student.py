from typing import Annotated

from fastapi import APIRouter, Depends

from ..dependencies.auth import get_current_user
from ..dependencies.dbExceptions import NotStudent
from ..models.User import Student, User


router = APIRouter()


@router.get("/student")
async def get_student(user: Annotated[User, Depends(get_current_user)]):
    try:
        return Student.get_student(user)
    except NotStudent:
        return {"Error": "No such student"}

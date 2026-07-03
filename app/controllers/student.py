from typing import Annotated

from fastapi import APIRouter, Depends

from app.dependencies.auth import get_current_user, require_mentor
from app.dependencies.dbExceptions import NotStudent
from app.models.User import Student, User


router = APIRouter()


@router.get("/student")
async def get_student(user: Annotated[User, Depends(get_current_user)]):
    try:
        return Student.get_student(user)
    except NotStudent:
        return {"Error": "No such student"}


@router.get("/students")
async def get_mentor_students(user: Annotated[User, Depends(require_mentor)]):
    return Student.get_students_by_mentor(user.user_id)

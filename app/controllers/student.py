from fastapi import APIRouter, Depends
from typing_extensions import Annotated

from ..dependencies.dbExceptions import NotStudent

from ..models.User import User, Student


router = APIRouter()


@router.get("/student")
async def get_student(user: Annotated[User, Depends(User.getUserData)]):
    try:
        return Student.get_student(user)
    except NotStudent:
        return {"Error": "No such student"}

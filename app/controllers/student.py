from fastapi import APIRouter, Depends
from typing_extensions import Annotated

from ..models.User import User, Student


router = APIRouter()


@router.get('/student')
def get_student(user: Annotated[str, Depends(User.getUserData)]):
    return user
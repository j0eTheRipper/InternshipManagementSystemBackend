from fastapi import APIRouter, HTTPException

from ..dependencies.auth import create_access_token
from ..dependencies.dbExceptions import IncorrectEmailOrPassword
from ..models.Credentials import Credentials
from ..models.User import Student, User


router = APIRouter()


@router.post("/login")
async def login(credentials: Credentials):
    if not credentials.email or not credentials.password:
        raise HTTPException(400, "email and password are required.")

    try:
        user_or_student = User.login(credentials.email, credentials.password)
        if isinstance(user_or_student, Student):
            user = user_or_student.user
            role = "student"
        else:
            user = user_or_student
            role = "universityMentor"
        token = create_access_token(user)
        return {
            "access_token": token,
            "token_type": "bearer",
            "user": user_or_student.model_dump(mode="json"),
            "role": role,
        }
    except IncorrectEmailOrPassword:
        raise HTTPException(401, "email or password incorrect!")

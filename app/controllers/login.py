from fastapi import APIRouter, HTTPException

from app.dependencies.auth import create_access_token
from app.dependencies.dbExceptions import IncorrectEmailOrPassword
from app.models.Credentials import Credentials
from app.models.PartneredCompanies.Headhunter import Headhunter
from app.models.Role import Role
from app.models.User import Student, User


router = APIRouter()


@router.post("/login")
async def login(credentials: Credentials):
    if not credentials.email or not credentials.password:
        raise HTTPException(400, "email and password are required.")

    try:
        user = User.login(credentials.email, credentials.password)
        if user.role == Role.student:
            user_or_student = Student.get_student(user)
            role = "student"
        elif user.role == Role.headhunter:
            user_or_student = Headhunter.get_headhunter(user)
            role = "headhunter"
        else:
            user_or_student = user
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

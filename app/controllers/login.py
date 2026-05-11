from fastapi import APIRouter, HTTPException

from app.dependencies.dbExceptions import IncorrectEmailOrPassword
from ..models.Credentials import Credentials
from ..models.User import User


router = APIRouter()


@router.post("/login")
async def login(credentials: Credentials):
    if not credentials.email or not credentials.password:
        raise HTTPException(400, "Username and password are required.")

    try:
        return User.login(credentials.email, credentials.password)
    except IncorrectEmailOrPassword:
        raise HTTPException(401, "email or password incorrect!")

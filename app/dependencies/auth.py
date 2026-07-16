from datetime import datetime, timedelta, timezone
from typing import Annotated

import jwt
from fastapi import Depends, HTTPException
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

from app.models.Role import Role
from app.models.User import User

SECRET_KEY = "change-me-in-production-32-bytes-min!"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_HOURS = 720

oauth2_scheme = HTTPBearer()


def create_access_token(user: User) -> str:
    payload = {
        "sub": str(user.user_id),
        "role": user.role.value,
        "exp": datetime.now(timezone.utc) + timedelta(hours=ACCESS_TOKEN_EXPIRE_HOURS),
    }
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)


async def get_current_user(auth: Annotated[HTTPAuthorizationCredentials, Depends(oauth2_scheme)]) -> User:
    try:
        payload = jwt.decode(auth.credentials, SECRET_KEY, algorithms=[ALGORITHM])
        user_id = payload.get("sub")
        if user_id is None:
            raise HTTPException(401, "Invalid token")
    except jwt.PyJWTError:
        raise HTTPException(401, "Invalid token")

    user = User.getUserData(int(user_id))
    return user


async def require_student(user: Annotated[User, Depends(get_current_user)]) -> User:
    if user.role != Role.student:
        raise HTTPException(403, "Only students can access this endpoint")
    return user


async def require_mentor(user: Annotated[User, Depends(get_current_user)]) -> User:
    if user.role != Role.universityMentor:
        raise HTTPException(403, "Only mentors can access this endpoint")
    return user


async def require_headhunter(user: Annotated[User, Depends(get_current_user)]) -> User:
    if user.role != Role.headhunter:
        raise HTTPException(403, "Only headhunters can access this endpoint")
    return user


async def require_admin(user: Annotated[User, Depends(get_current_user)]) -> User:
    if user.role != Role.admin:
        raise HTTPException(403, "Only admins can access this endpoint")
    return user


async def require_company_supervisor(user: Annotated[User, Depends(get_current_user)]) -> User:
    if user.role != Role.companySupervisor:
        raise HTTPException(403, "Only company supervisors can access this endpoint")
    return user

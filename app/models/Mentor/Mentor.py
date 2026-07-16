from typing import List, Optional

from fastapi import HTTPException
from pydantic import BaseModel

from app.dependencies import database_connector
from app.dependencies.dbExceptions import NotMentor
from app.models.Role import Role
from app.models.User import User


class Mentor(BaseModel):
    user: User

    @staticmethod
    def get_by_id(user_id: int) -> "Mentor":
        user = User.getUserData(user_id)
        if user.role != Role.universityMentor:
            raise NotMentor
        return Mentor(user=user)

    @staticmethod
    def get_all() -> List["Mentor"]:
        connection = database_connector.create_connection(False)
        rows = database_connector.execute_read(
            connection,
            "SELECT id, fullname, email, role FROM users WHERE role = 'universityMentor';",
        )
        if not rows:
            return []
        return [
            Mentor(user=User(user_id=r[0], fullname=r[1], email=r[2], role=r[3]))
            for r in rows
        ]

    @staticmethod
    def create(fullname: str, email: str, password: str) -> "Mentor":
        existing = User.get_by_email(email)
        if existing:
            raise HTTPException(409, "Email already registered")
        user = User.create(fullname, email, password, Role.universityMentor)
        return Mentor(user=user)

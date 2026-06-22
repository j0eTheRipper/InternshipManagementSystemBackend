from fastapi import HTTPException
from pydantic import BaseModel

from ..dependencies.dbExceptions import IncorrectEmailOrPassword, NotStudent

from .Role import Role
from ..dependencies import database_connector


class User(BaseModel):
    user_id: int
    fullname: str
    email: str
    role: Role

    @staticmethod
    def login(email: str, password: str):
        connection = database_connector.create_connection(False)
        row = database_connector.execute_read(
            connection,
            f"SELECT fullname, email, role, id FROM users WHERE email='{email}' and password='{password}';",
        )

        if not row:
            raise IncorrectEmailOrPassword

        row = row[0]

        user = User(fullname=row[0], email=row[1], role=row[2], user_id=int(row[3]))
        if user.role == Role.student:
            return Student.get_student(user)
        else:
            return user

    @staticmethod
    def getUserData(user_id: int):
        connection = database_connector.create_connection(False)
        row = database_connector.execute_read(
            connection,
            f"SELECT fullname, email, role, id FROM users WHERE id='{user_id}';",
        )

        if not row:
            raise HTTPException(404, "user not found")

        row = row[0]

        return User(fullname=row[0], email=row[1], role=row[2], user_id=row[3])


class Student(BaseModel):
    user: User
    university_mentor: User
    year_of_study: int
    field_of_study: str
    student_id: str
    progress: str

    @staticmethod
    def get_student(user: User):
        if user.role != Role.student:
            raise NotStudent

        connection = database_connector.create_connection(False)
        row = database_connector.execute_read(
            connection,
            f"SELECT year_of_study, field_of_study, student_id, university_mentor_id, progress FROM student WHERE user_id = {user.user_id};",
        )

        if not row:
            raise NotStudent

        row = row[0]

        university_mentor_user = User.getUserData(row[3])

        return Student(
            user=user,
            university_mentor=university_mentor_user,
            year_of_study=row[0],
            field_of_study=row[1],
            student_id=row[2],
            progress=row[4],
        )

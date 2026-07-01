from fastapi import HTTPException
from psycopg2 import DatabaseError
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
        elif user.role == Role.headhunter:
            from .Headhunter import Headhunter
            return Headhunter.get_headhunter(user)
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

    @staticmethod
    def get_by_email(email: str):
        connection = database_connector.create_connection(False)
        row = database_connector.execute_read(
            connection,
            f"SELECT fullname, email, role, id FROM users WHERE email = '{email}';",
        )
        if not row:
            return None
        row = row[0]
        return User(fullname=row[0], email=row[1], role=row[2], user_id=row[3])

    @staticmethod
    def create(fullname: str, email: str, password: str, role):
        connection = database_connector.create_connection(False)
        database_connector.execute_write(
            connection,
            f"INSERT INTO users (fullname, email, password, role) "
            f"VALUES ('{fullname}', '{email}', '{password}', '{role.value}');",
        )
        return User.get_by_email(email)


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

    @staticmethod
    def get_student_by_id(student_id: str):
        connection = database_connector.create_connection(False)
        row = database_connector.execute_read(
            connection,
            f"SELECT user_id, year_of_study, field_of_study, university_mentor_id, progress FROM student WHERE student_id = '{student_id}';",
        )

        if not row:
            raise HTTPException(404, "student not found")

        row = row[0]
        user = User.getUserData(row[0])
        university_mentor_user = User.getUserData(row[3])

        return Student(
            user=user,
            university_mentor=university_mentor_user,
            year_of_study=row[1],
            field_of_study=row[2],
            student_id=student_id,
            progress=row[4],
        )

    @staticmethod
    def get_students_by_mentor(mentor_id: int):
        connection = database_connector.create_connection(False)
        rows = database_connector.execute_read(
            connection,
            f"SELECT user_id, year_of_study, field_of_study, student_id, progress FROM student WHERE university_mentor_id = {mentor_id};",
        )

        if not rows:
            return []

        students = []
        for row in rows:
            user = User.getUserData(row[0])
            university_mentor_user = User.getUserData(mentor_id)
            students.append(
                Student(
                    user=user,
                    university_mentor=university_mentor_user,
                    year_of_study=row[1],
                    field_of_study=row[2],
                    student_id=row[3],
                    progress=row[4],
                )
            )

        return students

    @staticmethod
    def update_student_progress(student_id: str):
        connection = database_connector.create_connection(False)
        update_student_progres = f"UPDATE student SET progress = 'application' WHERE student_id = '{student_id}'"
        database_connector.execute_write(connection, update_student_progres)

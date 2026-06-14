from pydantic import BaseModel

from ..dependencies.dbExceptions import IncorrectEmailOrPassword

from .Role import Role
from ..dependencies import database_connector


class User(BaseModel):
    username: str
    password: str
    fullname: str
    email: str
    role: Role

    @staticmethod
    def login(email: str, password: str):
        connection = database_connector.create_connection(False)
        row = database_connector.execute_read(
            connection,
            f"SELECT username, fullname, email, password, role FROM users WHERE email='{email}' and password='{password}';",
        )

        if not row:
            raise IncorrectEmailOrPassword

        row = row[0]

        return User(
            username=row[0],
            fullname=row[1],
            email=row[2],
            password=row[3],
            role=row[4],
        )

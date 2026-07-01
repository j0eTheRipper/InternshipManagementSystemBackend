from fastapi import HTTPException
from pydantic import BaseModel

from ..dependencies import database_connector
from ..dependencies.dbExceptions import NotHeadhunter
from .Company import Company
from .Role import Role
from .User import User


class Headhunter(BaseModel):
    user: User
    company: Company

    @staticmethod
    def get_headhunter(user: User):
        if user.role != Role.headhunter:
            raise NotHeadhunter

        connection = database_connector.create_connection(False)
        row = database_connector.execute_read(
            connection,
            f"SELECT company_id FROM headhunter WHERE user_id = {user.user_id};",
        )
        if not row:
            raise HTTPException(404, "headhunter not found")

        company = Company.get_by_id(row[0][0])
        return Headhunter(user=user, company=company)

    @staticmethod
    def create(user_id: int, company_id: int):
        connection = database_connector.create_connection(False)
        database_connector.execute_write(
            connection,
            f"INSERT INTO headhunter (user_id, company_id) VALUES ({user_id}, {company_id});",
        )

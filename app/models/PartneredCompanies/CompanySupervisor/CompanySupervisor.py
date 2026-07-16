from fastapi import HTTPException
from pydantic import BaseModel

from app.dependencies import database_connector
from app.dependencies.dbExceptions import NotCompanySupervisor
from app.models.PartneredCompanies.Company import Company
from app.models.Role import Role
from app.models.User import User


class CompanySupervisor(BaseModel):
    user: User
    company: Company

    @staticmethod
    def get_company_supervisor(user: User):
        if user.role != Role.companySupervisor:
            raise NotCompanySupervisor

        connection = database_connector.create_connection(False)
        row = database_connector.execute_read(
            connection,
            f"SELECT company_id FROM company_supervisor WHERE user_id = {user.user_id};",
        )
        if not row:
            raise HTTPException(404, "company supervisor not found")

        company = Company.get_by_id(row[0][0])
        return CompanySupervisor(user=user, company=company)

    @staticmethod
    def get_by_id(user_id: int):
        connection = database_connector.create_connection(False)
        row = database_connector.execute_read(
            connection,
            f"SELECT user_id, company_id FROM company_supervisor WHERE user_id = {user_id};",
        )
        if not row:
            return None
        user = User.getUserData(row[0][0])
        company = Company.get_by_id(row[0][1])
        return CompanySupervisor(user=user, company=company)

    @staticmethod
    def get_all():
        connection = database_connector.create_connection(False)
        rows = database_connector.execute_read(
            connection,
            "SELECT user_id, company_id FROM company_supervisor;",
        )
        if not rows:
            return []
        supervisors = []
        for row in rows:
            user = User.getUserData(row[0])
            company = Company.get_by_id(row[1])
            supervisors.append(CompanySupervisor(user=user, company=company))
        return supervisors

    @staticmethod
    def create(user_id: int, company_id: int):
        connection = database_connector.create_connection(False)
        database_connector.execute_write(
            connection,
            f"INSERT INTO company_supervisor (user_id, company_id) VALUES ({user_id}, {company_id});",
        )

    @staticmethod
    def delete(user_id: int):
        connection = database_connector.create_connection(False)
        database_connector.execute_write(
            connection,
            f"DELETE FROM company_supervisor WHERE user_id = {user_id};",
        )

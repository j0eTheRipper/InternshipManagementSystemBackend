from fastapi import HTTPException
from pydantic import BaseModel

from app.dependencies import database_connector


class Application(BaseModel):
    application_id: int
    student_id: str
    opportunity_id: int | None = None
    resume_id: int
    status: str

    @staticmethod
    def create(student_id: str, opportunity_id: int, resume_id: int):
        connection = database_connector.create_connection(False)
        try:
            database_connector.execute_write(
                connection,
                f"INSERT INTO application (student_id, opportunity_id, resume_id, status) "
                f"VALUES ('{student_id}', {opportunity_id}, {resume_id}, 'pending');",
            )
        except Exception:
            raise HTTPException(409, "You have already applied to this opportunity")

        return Application.get_last_by_student(student_id)

    @staticmethod
    def create_external(student_id: str, resume_id: int):
        connection = database_connector.create_connection(False)
        database_connector.execute_write(
            connection,
            f"INSERT INTO application (student_id, opportunity_id, resume_id, status) "
            f"VALUES ('{student_id}', NULL, {resume_id}, 'pending');",
        )
        return Application.get_last_by_student(student_id)

    @staticmethod
    def get_last_by_student(student_id: str):
        connection = database_connector.create_connection(False)
        row = database_connector.execute_read(
            connection,
            f"SELECT application_id, student_id, opportunity_id, resume_id, status "
            f"FROM application WHERE student_id = '{student_id}' "
            f"ORDER BY application_id DESC LIMIT 1;",
        )
        if not row:
            return None
        row = row[0]
        return Application(
            application_id=row[0], student_id=row[1],
            opportunity_id=row[2], resume_id=row[3], status=row[4],
        )

    @staticmethod
    def get_by_id(application_id: int):
        connection = database_connector.create_connection(False)
        row = database_connector.execute_read(
            connection,
            f"SELECT application_id, student_id, opportunity_id, resume_id, status "
            f"FROM application WHERE application_id = {application_id};",
        )
        if not row:
            return None
        row = row[0]
        return Application(
            application_id=row[0], student_id=row[1],
            opportunity_id=row[2], resume_id=row[3], status=row[4],
        )

    @staticmethod
    def get_by_student(student_id: str):
        connection = database_connector.create_connection(False)
        rows = database_connector.execute_read(
            connection,
            f"SELECT application_id, student_id, opportunity_id, resume_id, status "
            f"FROM application WHERE student_id = '{student_id}' ORDER BY application_id DESC;",
        )
        return [
            Application(
                application_id=r[0], student_id=r[1],
                opportunity_id=r[2], resume_id=r[3], status=r[4],
            )
            for r in rows
        ]

    @staticmethod
    def get_by_opportunity(opportunity_id: int):
        connection = database_connector.create_connection(False)
        rows = database_connector.execute_read(
            connection,
            f"SELECT application_id, student_id, opportunity_id, resume_id, status "
            f"FROM application WHERE opportunity_id = {opportunity_id} ORDER BY application_id DESC;",
        )
        return [
            Application(
                application_id=r[0], student_id=r[1],
                opportunity_id=r[2], resume_id=r[3], status=r[4],
            )
            for r in rows
        ]

    @staticmethod
    def update_status(application_id: int, status: str):
        connection = database_connector.create_connection(False)
        database_connector.execute_write(
            connection,
            f"UPDATE application SET status = '{status}' WHERE application_id = {application_id};",
        )

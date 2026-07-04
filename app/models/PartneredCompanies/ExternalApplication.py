from pydantic import BaseModel

from app.dependencies import database_connector


class ExternalApplication(BaseModel):
    application_id: int
    company_name: str
    job_title: str
    job_mode: str
    company_location: str
    application_screenshot: str

    @staticmethod
    def create(application_id: int, company_name: str, job_title: str, job_mode: str, company_location: str, application_screenshot: str):
        connection = database_connector.create_connection(False)
        database_connector.execute_write(
            connection,
            f"INSERT INTO external_application (application_id, company_name, job_title, job_mode, company_location, application_screenshot) "
            f"VALUES ({application_id}, '{company_name}', '{job_title}', '{job_mode}', '{company_location}', '{application_screenshot}');",
        )

    @staticmethod
    def get_by_application_id(application_id: int):
        connection = database_connector.create_connection(False)
        row = database_connector.execute_read(
            connection,
            f"SELECT application_id, company_name, job_title, job_mode, company_location, application_screenshot "
            f"FROM external_application WHERE application_id = {application_id};",
        )
        if not row:
            return None
        row = row[0]
        return ExternalApplication(
            application_id=row[0], company_name=row[1], job_title=row[2],
            job_mode=row[3], company_location=row[4], application_screenshot=row[5],
        )

    @staticmethod
    def exists(student_id: str, company_name: str, job_title: str) -> bool:
        connection = database_connector.create_connection(False)
        row = database_connector.execute_read(
            connection,
            f"SELECT 1 FROM external_application ea "
            f"JOIN application a ON ea.application_id = a.application_id "
            f"WHERE a.student_id = '{student_id}' "
            f"AND LOWER(ea.company_name) = LOWER('{company_name}') "
            f"AND LOWER(ea.job_title) = LOWER('{job_title}');",
        )
        return len(row) > 0

    @staticmethod
    def delete(application_id: int):
        connection = database_connector.create_connection(False)
        database_connector.execute_write(
            connection,
            f"DELETE FROM external_application WHERE application_id = {application_id};",
        )

from pydantic import BaseModel

from app.dependencies import database_connector


_SELECT_COLS = "opportunity_id, title, job_role, description, location, status, headhunter_id, field_of_study, created_at"


class JobOpportunity(BaseModel):
    opportunity_id: int
    title: str
    job_role: str
    description: str
    location: str
    status: str
    headhunter_id: int
    field_of_study: str
    created_at: str | None = None

    @staticmethod
    def _from_row(row):
        return JobOpportunity(
            opportunity_id=row[0], title=row[1], job_role=row[2],
            description=row[3], location=row[4], status=row[5],
            headhunter_id=row[6], field_of_study=row[7],
            created_at=str(row[8]) if row[8] else None,
        )

    @staticmethod
    def create(title: str, job_role: str, description: str, location: str, status: str, field_of_study: str, headhunter_id: int):
        connection = database_connector.create_connection(False)
        database_connector.execute_write(
            connection,
            f"INSERT INTO job_opportunity (title, job_role, description, location, status, headhunter_id, field_of_study) "
            f"VALUES ('{title}', '{job_role}', '{description}', '{location}', '{status}', {headhunter_id}, '{field_of_study}');",
        )
        return JobOpportunity.get_last_by_headhunter(headhunter_id)

    @staticmethod
    def get_last_by_headhunter(headhunter_id: int):
        connection = database_connector.create_connection(False)
        row = database_connector.execute_read(
            connection,
            f"SELECT {_SELECT_COLS} FROM job_opportunity WHERE headhunter_id = {headhunter_id} "
            f"ORDER BY opportunity_id DESC LIMIT 1;",
        )
        if not row:
            return None
        return JobOpportunity._from_row(row[0])

    @staticmethod
    def get_by_id(opportunity_id: int):
        connection = database_connector.create_connection(False)
        row = database_connector.execute_read(
            connection,
            f"SELECT {_SELECT_COLS} FROM job_opportunity WHERE opportunity_id = {opportunity_id};",
        )
        if not row:
            return None
        return JobOpportunity._from_row(row[0])

    @staticmethod
    def get_all():
        connection = database_connector.create_connection(False)
        rows = database_connector.execute_read(
            connection,
            f"SELECT {_SELECT_COLS} FROM job_opportunity ORDER BY created_at DESC;",
        )
        return [JobOpportunity._from_row(r) for r in rows]

    @staticmethod
    def get_all_by_field(field_of_study: str):
        connection = database_connector.create_connection(False)
        rows = database_connector.execute_read(
            connection,
            f"SELECT {_SELECT_COLS} FROM job_opportunity "
            f"WHERE field_of_study = '{field_of_study}' ORDER BY created_at DESC;",
        )
        return [JobOpportunity._from_row(r) for r in rows]

    @staticmethod
    def get_paginated(field_of_study: str, limit: int, offset: int):
        connection = database_connector.create_connection(False)
        rows = database_connector.execute_read(
            connection,
            f"SELECT {_SELECT_COLS} FROM job_opportunity "
            f"WHERE field_of_study = '{field_of_study}' ORDER BY created_at DESC "
            f"LIMIT {limit} OFFSET {offset};",
        )
        return [JobOpportunity._from_row(r) for r in rows]

    @staticmethod
    def get_paginated_others(field_of_study: str, limit: int, offset: int):
        connection = database_connector.create_connection(False)
        rows = database_connector.execute_read(
            connection,
            f"SELECT {_SELECT_COLS} FROM job_opportunity "
            f"WHERE field_of_study != '{field_of_study}' ORDER BY created_at DESC "
            f"LIMIT {limit} OFFSET {offset};",
        )
        return [JobOpportunity._from_row(r) for r in rows]

    @staticmethod
    def get_by_headhunter(headhunter_id: int):
        connection = database_connector.create_connection(False)
        rows = database_connector.execute_read(
            connection,
            f"SELECT {_SELECT_COLS} FROM job_opportunity WHERE headhunter_id = {headhunter_id} ORDER BY created_at DESC;",
        )
        return [JobOpportunity._from_row(r) for r in rows]

    @staticmethod
    def update(opportunity_id: int, title: str, job_role: str, description: str, location: str, status: str):
        connection = database_connector.create_connection(False)
        database_connector.execute_write(
            connection,
            f"UPDATE job_opportunity SET title='{title}', job_role='{job_role}', "
            f"description='{description}', location='{location}', status='{status}' "
            f"WHERE opportunity_id = {opportunity_id};",
        )

    @staticmethod
    def delete(opportunity_id: int):
        connection = database_connector.create_connection(False)
        database_connector.execute_write(
            connection,
            f"DELETE FROM job_opportunity WHERE opportunity_id = {opportunity_id};",
        )

    def model_dump_with_company(self, company_name: str):
        data = self.model_dump(mode="json")
        data["company"] = company_name
        return data

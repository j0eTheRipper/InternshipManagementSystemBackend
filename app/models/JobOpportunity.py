from pydantic import BaseModel

from app.dependencies import database_connector


class JobOpportunity(BaseModel):
    opportunity_id: int
    title: str
    job_role: str
    description: str
    location: str
    status: str
    headhunter_id: int
    created_at: str | None = None

    @staticmethod
    def create(title: str, job_role: str, description: str, location: str, status: str, headhunter_id: int):
        connection = database_connector.create_connection(False)
        database_connector.execute_write(
            connection,
            f"INSERT INTO job_opportunity (title, job_role, description, location, status, headhunter_id) "
            f"VALUES ('{title}', '{job_role}', '{description}', '{location}', '{status}', {headhunter_id});",
        )
        return JobOpportunity.get_last_by_headhunter(headhunter_id)

    @staticmethod
    def get_last_by_headhunter(headhunter_id: int):
        connection = database_connector.create_connection(False)
        row = database_connector.execute_read(
            connection,
            f"SELECT opportunity_id, title, job_role, description, location, status, headhunter_id, created_at "
            f"FROM job_opportunity WHERE headhunter_id = {headhunter_id} "
            f"ORDER BY opportunity_id DESC LIMIT 1;",
        )
        if not row:
            return None
        row = row[0]
        return JobOpportunity(
            opportunity_id=row[0], title=row[1], job_role=row[2],
            description=row[3], location=row[4], status=row[5],
            headhunter_id=row[6], created_at=str(row[7]) if row[7] else None,
        )

    @staticmethod
    def get_by_id(opportunity_id: int):
        connection = database_connector.create_connection(False)
        row = database_connector.execute_read(
            connection,
            f"SELECT opportunity_id, title, job_role, description, location, status, headhunter_id, created_at "
            f"FROM job_opportunity WHERE opportunity_id = {opportunity_id};",
        )
        if not row:
            return None
        row = row[0]
        return JobOpportunity(
            opportunity_id=row[0], title=row[1], job_role=row[2],
            description=row[3], location=row[4], status=row[5],
            headhunter_id=row[6], created_at=str(row[7]) if row[7] else None,
        )

    @staticmethod
    def get_all():
        connection = database_connector.create_connection(False)
        rows = database_connector.execute_read(
            connection,
            "SELECT opportunity_id, title, job_role, description, location, status, headhunter_id, created_at "
            "FROM job_opportunity ORDER BY created_at DESC;",
        )
        return [
            JobOpportunity(
                opportunity_id=r[0], title=r[1], job_role=r[2],
                description=r[3], location=r[4], status=r[5],
                headhunter_id=r[6], created_at=str(r[7]) if r[7] else None,
            )
            for r in rows
        ]

    @staticmethod
    def get_by_headhunter(headhunter_id: int):
        connection = database_connector.create_connection(False)
        rows = database_connector.execute_read(
            connection,
            f"SELECT opportunity_id, title, job_role, description, location, status, headhunter_id, created_at "
            f"FROM job_opportunity WHERE headhunter_id = {headhunter_id} ORDER BY created_at DESC;",
        )
        return [
            JobOpportunity(
                opportunity_id=r[0], title=r[1], job_role=r[2],
                description=r[3], location=r[4], status=r[5],
                headhunter_id=r[6], created_at=str(r[7]) if r[7] else None,
            )
            for r in rows
        ]

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

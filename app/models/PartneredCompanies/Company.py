from pydantic import BaseModel

from app.dependencies import database_connector


class Company(BaseModel):
    company_id: int
    name: str
    email: str

    @staticmethod
    def get_by_name(name: str):
        connection = database_connector.create_connection(False)
        row = database_connector.execute_read(
            connection,
            f"SELECT company_id, name, email FROM company WHERE name = '{name}';",
        )
        if not row:
            return None
        row = row[0]
        return Company(company_id=row[0], name=row[1], email=row[2])

    @staticmethod
    def get_by_id(company_id: int):
        connection = database_connector.create_connection(False)
        row = database_connector.execute_read(
            connection,
            f"SELECT company_id, name, email FROM company WHERE company_id = {company_id};",
        )
        if not row:
            return None
        row = row[0]
        return Company(company_id=row[0], name=row[1], email=row[2])

    @staticmethod
    def create(name: str, email: str):
        connection = database_connector.create_connection(False)
        database_connector.execute_write(
            connection,
            f"INSERT INTO company (name, email) VALUES ('{name}', '{email}');",
        )
        return Company.get_by_name(name)

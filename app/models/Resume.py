from os import path

from pydantic import BaseModel

from ..dependencies.database_connector import (
    create_connection,
    execute_read,
    execute_write,
)


class Resume(BaseModel):
    student_id: str
    file: bytes
    verified: bool

    @staticmethod
    def get_resume(student_id: str):
        connection = create_connection(False)
        query = f"SELECT resume_id, student_id, file, verified FROM resume WHERE student_id = {student_id};"
        result = execute_read(connection, query)

        print(result)

    @staticmethod
    def upload_resume_in_storage(file_name: str, resume_file: bytes):
        with open(file_name, "wb") as file:
            file.write(resume_file)

        return path.abspath(file_name)

    @staticmethod
    def save_resume_in_db(student_id: str, resume: str):
        connection = create_connection(False)
        query = f"INSERT INTO resume (student_id, file) VALUES ('{student_id}', '{resume}');"
        print(query)
        execute_write(connection, query)

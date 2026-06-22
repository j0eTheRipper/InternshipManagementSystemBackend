from os import path

from fastapi import HTTPException
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
        query = f"SELECT resume_id, student_id, file, verified FROM resume WHERE student_id = '{student_id}';"
        results = execute_read(connection, query)

        if not results:
            raise HTTPException(404, "student has no resume")

        resumes = map(
            lambda result: Resume(
                student_id=result[1], file=result[2], verified=result[3]
            ),
            results,
        )
        return list(resumes)

    @staticmethod
    def upload_resume_in_storage(file_name: str, resume_file: bytes):
        with open(file_name, "wb") as file:
            file.write(resume_file)

        return path.abspath(file_name)

    @staticmethod
    def save_resume_in_db(student_id: str, resume: str):
        connection = create_connection(False)
        query = f"INSERT INTO resume (student_id, file) VALUES ('{student_id}', '{resume}');"
        execute_write(connection, query)

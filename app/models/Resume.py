import os
from uuid import uuid4

from fastapi import HTTPException
from pydantic import BaseModel

from ..dependencies import database_connector

UPLOAD_DIR = "uploads/resumes"


class Resume(BaseModel):
    resume_id: int
    student_id: str
    file: str
    verified: bool = False

    @staticmethod
    def get_resume(student_id: str):
        connection = database_connector.create_connection(False)
        query = f"SELECT resume_id, student_id, file, verified FROM resume WHERE student_id = '{student_id}';"
        results = database_connector.execute_read(connection, query)

        if not results:
            raise HTTPException(404, "student has no resume")

        resumes = map(
            lambda result: Resume(
                resume_id=result[0],
                student_id=result[1],
                file=result[2],
                verified=result[3],
            ),
            results,
        )
        return list(resumes)

    @staticmethod
    def get_resume_by_id(resume_id: int):
        connection = database_connector.create_connection(False)
        query = f"SELECT resume_id, student_id, file, verified FROM resume WHERE resume_id = {resume_id};"
        results = database_connector.execute_read(connection, query)

        if not results:
            raise HTTPException(404, "resume not found")

        result = results[0]
        return Resume(
            resume_id=result[0],
            student_id=result[1],
            file=result[2],
            verified=result[3],
        )

    @staticmethod
    def upload_resume_in_storage(
        student_id: str, original_filename: str, resume_file: bytes
    ):
        ext = os.path.splitext(original_filename)[1] or ".pdf"
        filename = f"{student_id}_{uuid4().hex}{ext}"
        full_path = os.path.join(UPLOAD_DIR, filename)

        os.makedirs(UPLOAD_DIR, exist_ok=True)

        with open(full_path, "wb") as f:
            f.write(resume_file)

        return os.path.abspath(full_path)

    @staticmethod
    def save_resume_in_db(student_id: str, resume_path: str) -> int:
        connection = database_connector.create_connection(False)
        query = f"INSERT INTO resume (student_id, file) VALUES ('{student_id}', '{resume_path}');"
        database_connector.execute_write(connection, query)
        result = database_connector.execute_read(
            connection,
            f"SELECT MAX(resume_id) FROM resume WHERE student_id = '{student_id}';",
        )
        return result[0][0] if result else 0

    @staticmethod
    def approve_resume(resume_id: int):
        connection = database_connector.create_connection(False)
        query = f"UPDATE resume SET verified = true WHERE resume_id = {resume_id};"
        database_connector.execute_write(connection, query)

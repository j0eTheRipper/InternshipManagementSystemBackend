from typing import ClassVar

from app.dependencies import database_connector
from app.models.Document.Document import Document


class Resume(Document):
    resume_id: int

    _table: ClassVar[str] = "resume"
    _id_field: ClassVar[str] = "resume_id"
    _upload_dir: ClassVar[str] = "uploads/resumes"
    _allowed_extensions: ClassVar[set[str]] = {"pdf"}
    _columns: ClassVar[list[str]] = ["resume_id", "student_id", "file", "verified"]

    @staticmethod
    def save_in_db(student_id: str, file_path: str) -> int:
        connection = database_connector.create_connection(False)
        query = f"INSERT INTO resume (student_id, file) VALUES ('{student_id}', '{file_path}');"
        database_connector.execute_write(connection, query)
        result = database_connector.execute_read(
            connection,
            f"SELECT MAX(resume_id) FROM resume WHERE student_id = '{student_id}';",
        )
        return result[0][0] if result else 0

from typing import ClassVar

from app.dependencies import database_connector
from app.models.Document.Document import Document


class IndemnityLetter(Document):
    indemnity_letter_id: int

    _table: ClassVar[str] = "indemnity_letter"
    _id_field: ClassVar[str] = "indemnity_letter_id"
    _upload_dir: ClassVar[str] = "uploads/indemnity_letters"
    _allowed_extensions: ClassVar[set[str]] = {"pdf"}
    _columns: ClassVar[list[str]] = ["indemnity_letter_id", "student_id", "file", "verified"]

    @staticmethod
    def save_in_db(student_id: str, file_path: str) -> int:
        connection = database_connector.create_connection(False)
        query = f"INSERT INTO indemnity_letter (student_id, file) VALUES ('{student_id}', '{file_path}');"
        database_connector.execute_write(connection, query)
        result = database_connector.execute_read(
            connection,
            f"SELECT MAX(indemnity_letter_id) FROM indemnity_letter WHERE student_id = '{student_id}';",
        )
        return result[0][0] if result else 0

    @classmethod
    def delete_by_student(cls, student_id: str):
        existing = cls.get_by_student(student_id)
        if existing:
            import os
            doc = existing[0]
            if os.path.exists(doc.file):
                os.remove(doc.file)
            connection = database_connector.create_connection(False)
            database_connector.execute_write(
                connection,
                f"DELETE FROM {cls._table} WHERE student_id = '{student_id}';",
            )

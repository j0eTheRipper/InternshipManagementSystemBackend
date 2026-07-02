import os
from typing import ClassVar
from uuid import uuid4

from pydantic import BaseModel

from ..dependencies import database_connector


class Document(BaseModel):
    student_id: str
    file: str
    verified: bool = False

    _table: ClassVar[str] = ""
    _id_field: ClassVar[str] = ""
    _upload_dir: ClassVar[str] = ""
    _allowed_extensions: ClassVar[set[str]] = {"pdf"}
    _columns: ClassVar[list[str]] = []

    @staticmethod
    def save_in_db(**kwargs) -> int:
        raise NotImplementedError

    @classmethod
    def upload_in_storage(cls, student_id: str, original_filename: str, content: bytes) -> str:
        ext = os.path.splitext(original_filename)[1] or ".pdf"
        filename = f"{student_id}_{uuid4().hex}{ext}"
        os.makedirs(cls._upload_dir, exist_ok=True)
        full_path = os.path.join(cls._upload_dir, filename)
        with open(full_path, "wb") as f:
            f.write(content)
        return os.path.abspath(full_path)

    @classmethod
    def get_by_id(cls, doc_id: int):
        connection = database_connector.create_connection(False)
        columns_str = ", ".join(cls._columns)
        query = f"SELECT {columns_str} FROM {cls._table} WHERE {cls._id_field} = {doc_id};"
        results = database_connector.execute_read(connection, query)
        if not results:
            return None
        return cls._row_to_instance(results[0])

    @classmethod
    def get_by_student(cls, student_id: str):
        connection = database_connector.create_connection(False)
        columns_str = ", ".join(cls._columns)
        query = f"SELECT {columns_str} FROM {cls._table} WHERE student_id = '{student_id}' ORDER BY {cls._id_field} DESC;"
        results = database_connector.execute_read(connection, query)
        return [cls._row_to_instance(row) for row in results]

    @classmethod
    def approve(cls, doc_id: int):
        connection = database_connector.create_connection(False)
        query = f"UPDATE {cls._table} SET verified = true WHERE {cls._id_field} = {doc_id};"
        database_connector.execute_write(connection, query)

    @classmethod
    def get_pending_by_mentor(cls, mentor_id: int):
        connection = database_connector.create_connection(False)
        doc_table_cols = ", ".join(f"{cls._table}.{col}" for col in cls._columns)
        query = (
            f"SELECT {doc_table_cols}, users.fullname "
            f"FROM {cls._table} "
            f"JOIN student ON {cls._table}.student_id = student.student_id "
            f"JOIN users ON student.university_mentor_id = users.id "
            f"WHERE student.university_mentor_id = {mentor_id} AND {cls._table}.verified = false;"
        )
        results = database_connector.execute_read(connection, query)
        return [
            {
                **dict(zip(cls._columns, r[:len(cls._columns)])),
                "student_name": r[-1],
            }
            for r in results
        ]

    @classmethod
    def _row_to_instance(cls, row: tuple):
        return cls(**dict(zip(cls._columns, row)))

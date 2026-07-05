from typing import ClassVar

from app.dependencies import database_connector
from app.models.Document.Document import Document


class OfferLetter(Document):
    offer_letter_id: int | None = None
    application_id: int

    _table: ClassVar[str] = "offer_letter"
    _id_field: ClassVar[str] = "offer_letter_id"
    _upload_dir: ClassVar[str] = "uploads/offer_letters"
    _allowed_extensions: ClassVar[set[str]] = {"pdf", "png", "jpg", "jpeg"}
    _columns: ClassVar[list[str]] = [
        "offer_letter_id", "application_id", "student_id", "file", "verified",
    ]

    @staticmethod
    def save_in_db(application_id: int, student_id: str, file_path: str) -> int:
        connection = database_connector.create_connection(False)
        query = (
            f"INSERT INTO offer_letter (application_id, student_id, file) "
            f"VALUES ({application_id}, '{student_id}', '{file_path}');"
        )
        database_connector.execute_write(connection, query)
        result = database_connector.execute_read(
            connection,
            f"SELECT MAX(offer_letter_id) FROM offer_letter WHERE application_id = {application_id};",
        )
        return result[0][0] if result else 0

    @classmethod
    def get_all_by_mentor(cls, mentor_id: int):
        connection = database_connector.create_connection(False)
        query = (
            f"SELECT {', '.join(f'{cls._table}.{c}' for c in cls._columns)}, "
            f"student_user.fullname, jo.title "
            f"FROM {cls._table} "
            f"JOIN student ON {cls._table}.student_id = student.student_id "
            f"JOIN users student_user ON student.user_id = student_user.id "
            f"JOIN application a ON {cls._table}.application_id = a.application_id "
            f"JOIN job_opportunity jo ON a.opportunity_id = jo.opportunity_id "
            f"WHERE student.university_mentor_id = {mentor_id};"
        )
        results = database_connector.execute_read(connection, query)
        n = len(cls._columns)
        return [
            {
                **dict(zip(cls._columns, r[:n])),
                "student_name": r[n],
                "opportunity_title": r[n + 1],
            }
            for r in results
        ]

    @classmethod
    def get_pending_by_mentor(cls, mentor_id: int):
        connection = database_connector.create_connection(False)
        query = (
            f"SELECT {', '.join(f'{cls._table}.{c}' for c in cls._columns)}, "
            f"student_user.fullname, jo.title "
            f"FROM {cls._table} "
            f"JOIN student ON {cls._table}.student_id = student.student_id "
            f"JOIN users student_user ON student.user_id = student_user.id "
            f"JOIN application a ON {cls._table}.application_id = a.application_id "
            f"JOIN job_opportunity jo ON a.opportunity_id = jo.opportunity_id "
            f"WHERE student.university_mentor_id = {mentor_id} AND {cls._table}.verified = false;"
        )
        results = database_connector.execute_read(connection, query)
        n = len(cls._columns)
        return [
            {
                **dict(zip(cls._columns, r[:n])),
                "student_name": r[n],
                "opportunity_title": r[n + 1],
            }
            for r in results
        ]

from pydantic import BaseModel

from app.dependencies import database_connector


class Attendance(BaseModel):
    attendance_id: int
    student_id: str
    checked_at: str | None = None

    @staticmethod
    def record(student_id: str):
        connection = database_connector.create_connection(False)
        database_connector.execute_write(
            connection,
            f"INSERT INTO attendance (student_id) VALUES ('{student_id}');",
        )
        results = database_connector.execute_read(
            connection,
            f"SELECT attendance_id, checked_at FROM attendance WHERE student_id = '{student_id}' ORDER BY attendance_id DESC LIMIT 1;",
        )
        if results:
            return Attendance(
                attendance_id=results[0][0],
                student_id=student_id,
                checked_at=str(results[0][1]) if results[0][1] else None,
            )
        return None

    @staticmethod
    def get_today(student_id: str):
        connection = database_connector.create_connection(False)
        query = (
            f"SELECT attendance_id, student_id, checked_at "
            f"FROM attendance "
            f"WHERE student_id = '{student_id}' "
            f"AND checked_at::date = CURRENT_DATE;"
        )
        results = database_connector.execute_read(connection, query)
        if not results:
            return None
        r = results[0]
        return Attendance(
            attendance_id=r[0],
            student_id=r[1],
            checked_at=str(r[2]) if r[2] else None,
        )

    @staticmethod
    def get_history(student_id: str):
        connection = database_connector.create_connection(False)
        query = (
            f"SELECT attendance_id, student_id, checked_at "
            f"FROM attendance "
            f"WHERE student_id = '{student_id}' "
            f"ORDER BY checked_at DESC;"
        )
        results = database_connector.execute_read(connection, query)
        return [
            Attendance(
                attendance_id=r[0],
                student_id=r[1],
                checked_at=str(r[2]) if r[2] else None,
            )
            for r in results
        ]

    @staticmethod
    def record_with_date(student_id: str, date_str: str):
        connection = database_connector.create_connection(False)
        database_connector.execute_write(
            connection,
            f"INSERT INTO attendance (student_id, checked_at) VALUES ('{student_id}', '{date_str}');",
        )
        results = database_connector.execute_read(
            connection,
            f"SELECT attendance_id, checked_at FROM attendance WHERE student_id = '{student_id}' AND checked_at::date = '{date_str}'::date ORDER BY attendance_id DESC LIMIT 1;",
        )
        if results:
            return Attendance(
                attendance_id=results[0][0],
                student_id=student_id,
                checked_at=str(results[0][1]) if results[0][1] else None,
            )
        return None

    @staticmethod
    def delete(attendance_id: int):
        connection = database_connector.create_connection(False)
        database_connector.execute_write(
            connection,
            f"DELETE FROM attendance WHERE attendance_id = {attendance_id};",
        )

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

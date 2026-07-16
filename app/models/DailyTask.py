from pydantic import BaseModel

from app.dependencies import database_connector


class DailyTask(BaseModel):
    daily_task_id: int
    student_id: str
    update_text: str
    update_date: str | None = None
    week_start_date: str | None = None
    week_end_date: str | None = None
    submitted_at: str | None = None
    verified: bool = False
    verified_by: int | None = None
    verified_at: str | None = None

    @staticmethod
    def submit(student_id: str, update_text: str, update_date: str, week_start_date: str, week_end_date: str):
        connection = database_connector.create_connection(False)
        database_connector.execute_write(
            connection,
            (
                f"INSERT INTO daily_task (student_id, update_text, update_date, week_start_date, week_end_date) "
                f"VALUES ('{student_id}', '{update_text}', '{update_date}', '{week_start_date}', '{week_end_date}') "
                f"ON CONFLICT (student_id, update_date) DO UPDATE "
                f"SET update_text = '{update_text}', submitted_at = NOW();"
            ),
        )
        results = database_connector.execute_read(
            connection,
            (
                f"SELECT daily_task_id, update_date, week_start_date, week_end_date, submitted_at, verified, verified_by, verified_at "
                f"FROM daily_task "
                f"WHERE student_id = '{student_id}' AND update_date = '{update_date}';"
            ),
        )
        if results:
            return DailyTask(
                daily_task_id=results[0][0],
                student_id=student_id,
                update_text=update_text,
                update_date=str(results[0][1]) if results[0][1] else None,
                week_start_date=str(results[0][2]) if results[0][2] else None,
                week_end_date=str(results[0][3]) if results[0][3] else None,
                submitted_at=str(results[0][4]) if results[0][4] else None,
                verified=results[0][5] or False,
                verified_by=results[0][6],
                verified_at=str(results[0][7]) if results[0][7] else None,
            )
        return None

    @staticmethod
    def get_history(student_id: str):
        connection = database_connector.create_connection(False)
        query = (
            f"SELECT daily_task_id, student_id, update_text, update_date, week_start_date, week_end_date, submitted_at, verified, verified_by, verified_at "
            f"FROM daily_task "
            f"WHERE student_id = '{student_id}' "
            f"ORDER BY update_date DESC;"
        )
        results = database_connector.execute_read(connection, query)
        return [
            DailyTask(
                daily_task_id=r[0],
                student_id=r[1],
                update_text=r[2],
                update_date=str(r[3]) if r[3] else None,
                week_start_date=str(r[4]) if r[4] else None,
                week_end_date=str(r[5]) if r[5] else None,
                submitted_at=str(r[6]) if r[6] else None,
                verified=r[7] or False,
                verified_by=r[8],
                verified_at=str(r[9]) if r[9] else None,
            )
            for r in results
        ]

    @staticmethod
    def get_by_date(student_id: str, update_date: str):
        connection = database_connector.create_connection(False)
        query = (
            f"SELECT daily_task_id, student_id, update_text, update_date, week_start_date, week_end_date, submitted_at, verified, verified_by, verified_at "
            f"FROM daily_task "
            f"WHERE student_id = '{student_id}' AND update_date = '{update_date}';"
        )
        results = database_connector.execute_read(connection, query)
        if not results:
            return None
        r = results[0]
        return DailyTask(
            daily_task_id=r[0],
            student_id=r[1],
            update_text=r[2],
            update_date=str(r[3]) if r[3] else None,
            week_start_date=str(r[4]) if r[4] else None,
            week_end_date=str(r[5]) if r[5] else None,
            submitted_at=str(r[6]) if r[6] else None,
            verified=r[7] or False,
            verified_by=r[8],
            verified_at=str(r[9]) if r[9] else None,
        )

    @staticmethod
    def verify(daily_task_id: int, verifier_id: int):
        connection = database_connector.create_connection(False)
        database_connector.execute_write(
            connection,
            f"UPDATE daily_task SET verified = TRUE, verified_by = {verifier_id}, verified_at = NOW() WHERE daily_task_id = {daily_task_id};",
        )

    @staticmethod
    def unverify(daily_task_id: int):
        connection = database_connector.create_connection(False)
        database_connector.execute_write(
            connection,
            f"UPDATE daily_task SET verified = FALSE, verified_by = NULL, verified_at = NULL WHERE daily_task_id = {daily_task_id};",
        )

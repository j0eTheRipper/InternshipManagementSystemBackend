from app.dependencies import database_connector
from app.models.User import User
from app.models.Role import Role


def can_chat(user_a_id: int, user_b_id: int) -> bool:
    if user_a_id == user_b_id:
        return False

    user_a = User.getUserData(user_a_id)
    user_b = User.getUserData(user_b_id)

    if user_a.role == Role.admin or user_b.role == Role.admin:
        return True

    if user_a.role == Role.student:
        connection = database_connector.create_connection(False)
        row = database_connector.execute_read(
            connection,
            f"SELECT university_mentor_id, company_supervisor_id FROM student WHERE user_id = {user_a_id};",
        )
        if not row:
            return False
        mentor_id = row[0][0]
        supervisor_id = row[0][1]
        return user_b_id == mentor_id or (supervisor_id is not None and user_b_id == supervisor_id)

    if user_a.role == Role.universityMentor:
        connection = database_connector.create_connection(False)
        rows = database_connector.execute_read(
            connection,
            f"SELECT user_id, company_supervisor_id FROM student WHERE university_mentor_id = {user_a_id};",
        )
        if not rows:
            return False
        for r in rows:
            if user_b_id == r[0]:
                return True
            if r[1] is not None and user_b_id == r[1]:
                return True
        return False

    if user_a.role == Role.companySupervisor:
        connection = database_connector.create_connection(False)
        rows = database_connector.execute_read(
            connection,
            f"SELECT user_id, university_mentor_id FROM student WHERE company_supervisor_id = {user_a_id};",
        )
        if not rows:
            return False
        for r in rows:
            if user_b_id == r[0]:
                return True
            if r[1] is not None and user_b_id == r[1]:
                return True
        return False

    return False

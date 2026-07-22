from fastapi.testclient import TestClient
from app.dependencies import auth
from app.models.Role import Role
from app.models.User import User
from app.main import app

client = TestClient(app)

mock_admin = User(
    user_id=100,
    fullname="Admin User",
    email="admin@system.com",
    role=Role.admin,
)

mock_mentor = User(
    user_id=200,
    fullname="Mentor User",
    email="mentor@example.com",
    role=Role.universityMentor,
)

mock_student_user = User(
    user_id=300,
    fullname="Student User",
    email="student@example.com",
    role=Role.student,
)


def _override(user):
    async def _fn():
        return user
    return _fn


# ── list students ─────────────────────────────────────────


def test_list_students_success(mocker):
    app.dependency_overrides[auth.get_current_user] = _override(mock_admin)
    try:
        mocker.patch(
            "app.dependencies.database_connector.execute_read",
            side_effect=[
                # get_all_students query
                [(300, 2, "CS", "TP0112233", "none", 200, None, None, None, None, None, None)],
                # getUserData for student user
                [("Student User", "student@example.com", "student", 300)],
                # getUserData for mentor
                [("Mentor User", "mentor@example.com", "universityMentor", 200)],
            ],
        )
        mocker.patch(
            "app.dependencies.database_connector.create_connection",
            return_value=None,
        )

        response = client.get("/admin/students")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["student_id"] == "TP0112233"
    finally:
        app.dependency_overrides.clear()


def test_list_students_empty(mocker):
    app.dependency_overrides[auth.get_current_user] = _override(mock_admin)
    try:
        mocker.patch(
            "app.dependencies.database_connector.execute_read",
            return_value=[],
        )
        mocker.patch(
            "app.dependencies.database_connector.create_connection",
            return_value=None,
        )

        response = client.get("/admin/students")
        assert response.status_code == 200
        assert response.json() == []
    finally:
        app.dependency_overrides.clear()


def test_list_students_not_admin():
    app.dependency_overrides[auth.get_current_user] = _override(mock_student_user)
    try:
        response = client.get("/admin/students")
        assert response.status_code == 403
    finally:
        app.dependency_overrides.clear()


def test_list_students_unauthenticated():
    response = client.get("/admin/students")
    assert response.status_code == 401


# ── create student ────────────────────────────────────────


def test_create_student_success(mocker):
    app.dependency_overrides[auth.get_current_user] = _override(mock_admin)
    try:
        mocker.patch(
            "app.dependencies.database_connector.execute_read",
            side_effect=[
                # get_by_email (no existing)
                [],
                # get_by_student_id (no existing)
                [],
                # User.getUserData for mentor
                [("Mentor User", "mentor@example.com", "universityMentor", 200)],
                # User.create -> get_by_email
                [("New Student", "new@example.com", "student", 400)],
            ],
        )
        mocker.patch(
            "app.dependencies.database_connector.create_connection",
            return_value=None,
        )
        mocker.patch(
            "app.dependencies.database_connector.execute_write",
            return_value=None,
        )

        response = client.post(
            "/admin/students",
            json={
                "fullname": "New Student",
                "email": "new@example.com",
                "password": "password123",
                "student_id": "TP0555666",
                "year_of_study": 3,
                "field_of_study": "Engineering",
                "mentor_id": 200,
            },
        )
        assert response.status_code == 200
        assert response.json()["message"] == "Student created"
    finally:
        app.dependency_overrides.clear()


def test_create_student_duplicate_email(mocker):
    app.dependency_overrides[auth.get_current_user] = _override(mock_admin)
    try:
        mocker.patch(
            "app.dependencies.database_connector.execute_read",
            side_effect=[
                # get_by_email finds existing user
                [("Existing", "dup@example.com", "student", 500)],
            ],
        )
        mocker.patch(
            "app.dependencies.database_connector.create_connection",
            return_value=None,
        )

        response = client.post(
            "/admin/students",
            json={
                "fullname": "Dup Student",
                "email": "dup@example.com",
                "password": "password123",
                "student_id": "TP0999000",
                "year_of_study": 2,
                "field_of_study": "CS",
                "mentor_id": 200,
            },
        )
        assert response.status_code == 409
    finally:
        app.dependency_overrides.clear()


def test_create_student_invalid_mentor(mocker):
    app.dependency_overrides[auth.get_current_user] = _override(mock_admin)
    try:
        mocker.patch(
            "app.dependencies.database_connector.execute_read",
            side_effect=[
                # get_by_email (no existing)
                [],
                # get_by_student_id (no existing)
                [],
            ],
        )
        mocker.patch(
            "app.dependencies.database_connector.create_connection",
            return_value=None,
        )
        mocker.patch(
            "app.models.User.User.getUserData",
            return_value=mock_student_user,
        )

        response = client.post(
            "/admin/students",
            json={
                "fullname": "Bad Student",
                "email": "bad@example.com",
                "password": "password123",
                "student_id": "TP0111111",
                "year_of_study": 1,
                "field_of_study": "Math",
                "mentor_id": 300,
            },
        )
        assert response.status_code == 400
    finally:
        app.dependency_overrides.clear()


# ── list mentors ──────────────────────────────────────────


def test_list_mentors_success(mocker):
    app.dependency_overrides[auth.get_current_user] = _override(mock_admin)
    try:
        mocker.patch(
            "app.dependencies.database_connector.execute_read",
            return_value=[(200, "Mentor User", "mentor@example.com", "universityMentor")],
        )
        mocker.patch(
            "app.dependencies.database_connector.create_connection",
            return_value=None,
        )

        response = client.get("/admin/mentors")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["fullname"] == "Mentor User"
    finally:
        app.dependency_overrides.clear()


def test_list_mentors_not_admin():
    app.dependency_overrides[auth.get_current_user] = _override(mock_mentor)
    try:
        response = client.get("/admin/mentors")
        assert response.status_code == 403
    finally:
        app.dependency_overrides.clear()


# ── create mentor ─────────────────────────────────────────


def test_create_mentor_success(mocker):
    app.dependency_overrides[auth.get_current_user] = _override(mock_admin)
    try:
        mocker.patch(
            "app.dependencies.database_connector.execute_read",
            side_effect=[
                # get_by_email (no existing)
                [],
                # User.create -> get_by_email
                [("New Mentor", "newmentor@example.com", "universityMentor", 600)],
            ],
        )
        mocker.patch(
            "app.dependencies.database_connector.create_connection",
            return_value=None,
        )
        mocker.patch(
            "app.dependencies.database_connector.execute_write",
            return_value=None,
        )

        response = client.post(
            "/admin/mentors",
            json={
                "fullname": "New Mentor",
                "email": "newmentor@example.com",
                "password": "password123",
            },
        )
        assert response.status_code == 200
        assert response.json()["message"] == "Mentor created"
    finally:
        app.dependency_overrides.clear()


def test_create_mentor_duplicate_email(mocker):
    app.dependency_overrides[auth.get_current_user] = _override(mock_admin)
    try:
        mocker.patch(
            "app.dependencies.database_connector.execute_read",
            return_value=[("Existing", "dup@example.com", "universityMentor", 700)],
        )
        mocker.patch(
            "app.dependencies.database_connector.create_connection",
            return_value=None,
        )

        response = client.post(
            "/admin/mentors",
            json={
                "fullname": "Dup Mentor",
                "email": "dup@example.com",
                "password": "password123",
            },
        )
        assert response.status_code == 409
    finally:
        app.dependency_overrides.clear()


# ── update progress ───────────────────────────────────────


def test_update_progress_success(mocker):
    app.dependency_overrides[auth.get_current_user] = _override(mock_admin)
    try:
        mocker.patch(
            "app.dependencies.database_connector.execute_write",
            return_value=None,
        )
        mocker.patch(
            "app.dependencies.database_connector.create_connection",
            return_value=None,
        )

        response = client.patch(
            "/admin/students/TP0112233/progress",
            json={"progress": "accepted"},
        )
        assert response.status_code == 200
        assert response.json()["message"] == "Progress updated"
    finally:
        app.dependency_overrides.clear()


def test_update_progress_invalid_value(mocker):
    app.dependency_overrides[auth.get_current_user] = _override(mock_admin)
    try:
        response = client.patch(
            "/admin/students/TP0112233/progress",
            json={"progress": "bogus"},
        )
        assert response.status_code == 400
    finally:
        app.dependency_overrides.clear()


# ── update mentor ─────────────────────────────────────────


def test_update_mentor_success(mocker):
    app.dependency_overrides[auth.get_current_user] = _override(mock_admin)
    try:
        mocker.patch(
            "app.models.User.User.getUserData",
            return_value=mock_mentor,
        )
        mocker.patch(
            "app.dependencies.database_connector.execute_write",
            return_value=None,
        )
        mocker.patch(
            "app.dependencies.database_connector.create_connection",
            return_value=None,
        )

        response = client.patch(
            "/admin/students/TP0112233/mentor",
            json={"mentor_id": 200},
        )
        assert response.status_code == 200
        assert response.json()["message"] == "Mentor updated"
    finally:
        app.dependency_overrides.clear()


def test_update_mentor_invalid_target(mocker):
    app.dependency_overrides[auth.get_current_user] = _override(mock_admin)
    try:
        mocker.patch(
            "app.models.User.User.getUserData",
            return_value=mock_student_user,
        )

        response = client.patch(
            "/admin/students/TP0112233/mentor",
            json={"mentor_id": 300},
        )
        assert response.status_code == 400
    finally:
        app.dependency_overrides.clear()


# ── get student detail ────────────────────────────────────


def test_get_student_detail_success(mocker):
    app.dependency_overrides[auth.get_current_user] = _override(mock_admin)
    try:
        mocker.patch(
            "app.dependencies.database_connector.execute_read",
            side_effect=[
                # get_student_by_id query
                [(300, 2, "CS", 200, "none", None, None, None, None, None, None)],
                # getUserData for student user
                [("Student User", "student@example.com", "student", 300)],
                # getUserData for mentor
                [("Mentor User", "mentor@example.com", "universityMentor", 200)],
            ],
        )
        mocker.patch(
            "app.dependencies.database_connector.create_connection",
            return_value=None,
        )

        response = client.get("/admin/students/TP0112233")
        assert response.status_code == 200
        assert response.json()["student_id"] == "TP0112233"
    finally:
        app.dependency_overrides.clear()


# ── attendance management ─────────────────────────────────


def test_add_attendance_success(mocker):
    app.dependency_overrides[auth.get_current_user] = _override(mock_admin)
    try:
        mocker.patch(
            "app.dependencies.database_connector.execute_read",
            side_effect=[
                # get_student_by_id
                [(300, 2, "CS", 200, "accepted", None, None, None, None, None, None)],
                # getUserData for student user
                [("Student User", "student@example.com", "student", 300)],
                # getUserData for mentor
                [("Mentor User", "mentor@example.com", "universityMentor", 200)],
                # record_with_date fetch
                [(1, "2024-07-15 09:00:00")],
            ],
        )
        mocker.patch(
            "app.dependencies.database_connector.create_connection",
            return_value=None,
        )
        mocker.patch(
            "app.dependencies.database_connector.execute_write",
            return_value=None,
        )

        response = client.post(
            "/admin/attendance",
            json={"student_id": "TP0112233", "date": "2024-07-15"},
        )
        assert response.status_code == 200
        assert response.json()["message"] == "Attendance added"
    finally:
        app.dependency_overrides.clear()


def test_delete_attendance_success(mocker):
    app.dependency_overrides[auth.get_current_user] = _override(mock_admin)
    try:
        mocker.patch(
            "app.dependencies.database_connector.execute_write",
            return_value=None,
        )
        mocker.patch(
            "app.dependencies.database_connector.create_connection",
            return_value=None,
        )

        response = client.delete("/admin/attendance/42")
        assert response.status_code == 200
        assert response.json()["message"] == "Attendance deleted"
    finally:
        app.dependency_overrides.clear()


def test_get_student_attendance_success(mocker):
    app.dependency_overrides[auth.get_current_user] = _override(mock_admin)
    try:
        mocker.patch(
            "app.dependencies.database_connector.execute_read",
            side_effect=[
                # get_student_by_id: student record
                [(300, 2, "CS", 200, "accepted", "2024-07-01", 12, None, None, None, None)],
                # getUserData for student user
                [("Student User", "student@example.com", "student", 300)],
                # getUserData for mentor
                [("Mentor User", "mentor@example.com", "universityMentor", 200)],
                # Attendance.get_history
                [
                    (1, "TP0112233", "2024-07-15 09:00:00", False, None, None),
                    (2, "TP0112233", "2024-07-12 08:30:00", False, None, None),
                ],
            ],
        )
        mocker.patch(
            "app.dependencies.database_connector.create_connection",
            return_value=None,
        )

        response = client.get("/admin/attendance/TP0112233")
        assert response.status_code == 200
        data = response.json()
        assert len(data) > 0
        attended = [r for r in data if r["attended"]]
        missed = [r for r in data if not r["attended"] and not r["pending"]]
        assert len(attended) == 2
        assert len(missed) > 0
        assert data[0]["date"] is not None
    finally:
        app.dependency_overrides.clear()


def test_admin_attendance_not_admin():
    app.dependency_overrides[auth.get_current_user] = _override(mock_student_user)
    try:
        response = client.get("/admin/attendance/TP0112233")
        assert response.status_code == 403
    finally:
        app.dependency_overrides.clear()

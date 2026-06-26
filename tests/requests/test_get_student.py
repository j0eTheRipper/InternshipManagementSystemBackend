from fastapi.testclient import TestClient
from app.dependencies import auth
from app.models.Role import Role
from app.models.User import User
from app.main import app

client = TestClient(app)

mock_student_user = User(
    user_id=1,
    fullname="John Doe",
    email="john@example.com",
    role=Role.student,
)

mock_mentor_user = User(
    user_id=2,
    fullname="Jane Smith",
    email="jane@example.com",
    role=Role.universityMentor,
)


def _override_user(user):
    async def override():
        return user
    return override


def test_get_student_success(mocker):
    app.dependency_overrides[auth.get_current_user] = _override_user(
        mock_student_user
    )
    try:
        mocker.patch(
            "app.dependencies.database_connector.execute_read",
            side_effect=[
                [(2, "software engineer", "TP0112233", 999, "none")],
                [("Mentor One", "mentor@example.com", "universityMentor", 999)],
            ],
        )
        mocker.patch(
            "app.dependencies.database_connector.create_connection",
            return_value=None,
        )

        response = client.get("/student")

        assert response.status_code == 200
        assert response.json() == {
            "user": {
                "user_id": 1,
                "fullname": "John Doe",
                "email": "john@example.com",
                "role": "student",
            },
            "university_mentor": {
                "user_id": 999,
                "fullname": "Mentor One",
                "email": "mentor@example.com",
                "role": "universityMentor",
            },
            "year_of_study": 2,
            "field_of_study": "software engineer",
            "student_id": "TP0112233",
            "progress": "none",
        }
    finally:
        app.dependency_overrides.clear()


def test_get_student_not_student(mocker):
    app.dependency_overrides[auth.get_current_user] = _override_user(
        mock_mentor_user
    )
    try:
        response = client.get("/student")
        assert response.status_code == 200
        assert response.json() == {"Error": "No such student"}
    finally:
        app.dependency_overrides.clear()


def test_get_student_student_record_not_found(mocker):
    app.dependency_overrides[auth.get_current_user] = _override_user(
        mock_student_user
    )
    try:
        mocker.patch(
            "app.dependencies.database_connector.execute_read",
            return_value=[],
        )
        mocker.patch(
            "app.dependencies.database_connector.create_connection",
            return_value=None,
        )

        response = client.get("/student")
        assert response.status_code == 200
        assert response.json() == {"Error": "No such student"}
    finally:
        app.dependency_overrides.clear()


def test_get_student_not_authenticated():
    response = client.get("/student")
    assert response.status_code == 401


def test_get_student_wrong_method():
    response = client.post("/student")
    assert response.status_code == 405

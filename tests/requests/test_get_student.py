import pytest
from fastapi.testclient import TestClient
from app.dependencies.dbExceptions import IncorrectEmailOrPassword, NotStudent
from app.main import app

client = TestClient(app)


def test_get_student_success(mocker):
    mocker.patch(
        "app.dependencies.database_connector.execute_read",
        side_effect=[
            [("John Doe", "john@example.com", "student", 1)],
            [(2, "software engineer", "TP0112233", 999, "none")],
            [("Mentor One", "mentor@example.com", "universityMentor", 999)],
        ],
    )
    mocker.patch(
        "app.dependencies.database_connector.create_connection", return_value=None
    )

    response = client.get("/student?user_id=1")

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


def test_get_student_not_student(mocker):
    mocker.patch(
        "app.dependencies.database_connector.execute_read",
        return_value=[("Jane Smith", "jane@example.com", "universityMentor", 2)],
    )
    mocker.patch(
        "app.dependencies.database_connector.create_connection", return_value=None
    )

    with pytest.raises(NotStudent):
        client.get("/student?user_id=2")


def test_get_student_student_record_not_found(mocker):
    mocker.patch(
        "app.dependencies.database_connector.execute_read",
        side_effect=[
            [("John Doe", "john@example.com", "student", 1)],
            [],
        ],
    )
    mocker.patch(
        "app.dependencies.database_connector.create_connection", return_value=None
    )

    with pytest.raises(NotStudent):
        client.get("/student?user_id=1")


def test_get_student_user_not_found(mocker):
    mocker.patch(
        "app.dependencies.database_connector.execute_read", return_value=[]
    )
    mocker.patch(
        "app.dependencies.database_connector.create_connection", return_value=None
    )

    with pytest.raises(IncorrectEmailOrPassword):
        client.get("/student?user_id=999")


def test_get_student_missing_user_id():
    response = client.get("/student")

    assert response.status_code == 422


def test_get_student_wrong_method():
    response = client.post("/student")

    assert response.status_code == 405

import pytest
from fastapi.testclient import TestClient
from app.dependencies.dbExceptions import IncorrectEmailOrPassword
from app.main import app

client = TestClient(app)


def test_get_student_success(mocker):
    mocker.patch(
        "app.dependencies.database_connector.execute_read",
        return_value=[("John Doe", "john@example.com", "student", 1)],
    )
    mocker.patch(
        "app.dependencies.database_connector.create_connection", return_value=None
    )

    response = client.get("/student?user_id=1")

    assert response.status_code == 200
    assert response.json() == {
        "user_id": 1,
        "fullname": "John Doe",
        "email": "john@example.com",
        "role": "student",
    }


def test_get_student_returns_mentor_user(mocker):
    mocker.patch(
        "app.dependencies.database_connector.execute_read",
        return_value=[("Jane Smith", "jane@example.com", "universityMentor", 2)],
    )
    mocker.patch(
        "app.dependencies.database_connector.create_connection", return_value=None
    )

    response = client.get("/student?user_id=2")

    assert response.status_code == 200
    assert response.json() == {
        "user_id": 2,
        "fullname": "Jane Smith",
        "email": "jane@example.com",
        "role": "universityMentor",
    }


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

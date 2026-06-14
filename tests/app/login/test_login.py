from fastapi.testclient import TestClient
from app.dependencies import database_connector
from app.models.Role import Role
from app.models.User import User
from app.main import app


client = TestClient(app)


def test_login():
    response = client.get("/login/")

    assert response.status_code == 405


def test_login_wrong_credentials(mocker):
    mocker.patch.object(database_connector, "create_connection", return_value=None)
    mocker.patch.object(database_connector, "execute_read", return_value=None)
    response = client.post(
        "/login",
        json={"email": "wrong-email@gmail.com", "password": "wrong-password"},
    )

    assert response.status_code == 401
    assert response.json() == {"detail": "email or password incorrect!"}


def test_login_correct_credentials(mocker):
    mock_user = User(
        password="password",
        fullname="fullname",
        email="email@email.email",
        role=Role.student,
    )

    mocker.patch.object(User, "login", return_value=mock_user)

    response = client.post(
        "/login",
        json={"email": "correctemail@gmail.com", "password": "123123123"},
    )

    assert response.status_code == 200
    assert response.json() == {
        "password": "password",
        "fullname": "fullname",
        "email": "email@email.email",
        "role": "student",
    }


def test_login_blank_credential():
    response = client.post(
        "/login",
        json={"email": "", "password": ""},
    )

    assert response.status_code == 400
    assert response.json() == {"detail": "email and password are required."}

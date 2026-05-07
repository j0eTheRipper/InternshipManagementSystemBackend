from fastapi.testclient import TestClient
from app.login.models import Role, User
from app.main import app


client = TestClient(app)


def test_login():
    response = client.get("/login/")

    assert response.status_code == 405


def test_login_wrong_credentials():
    response = client.post(
        "/login",
        json={"email": "wrong-email@gmail.com", "password": "wrong-password"},
    )

    assert response.status_code == 401
    assert response.json() == {"detail": "email or password incorrect!"}


def test_login_correct_credentials(mocker):
    mock_user = User(
        username="user",
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
        "username": "user",
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
    assert response.json() == {"detail": "Username and password are required."}

from fastapi.testclient import TestClient
from app.dependencies import database_connector
from app.models.Role import Role
from app.models.User import User, Student
from app.main import app


client = TestClient(app)

mock_mentor = User(
    user_id=1,
    fullname="mentor1",
    email="email@email.email",
    role=Role.universityMentor,
)


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


def test_login_correct_credentials_mentor(mocker):
    mock_user = mock_mentor
    mocker.patch.object(User, "login", return_value=mock_user)

    response = client.post(
        "/login",
        json={"email": "correctemail@gmail.com", "password": "123123123"},
    )

    assert response.status_code == 200
    assert response.json() == {
        "fullname": "mentor1",
        "email": "email@email.email",
        "role": "universityMentor",
        "user_id": 1,
    }


def test_login_correct_student(mocker):
    mock_user = User(
        fullname="fullname",
        email="Studentemail@email.email",
        role=Role.student,
        user_id=1,
    )

    mock_student = Student(
        user=mock_user,
        university_mentor=mock_mentor,
        year_of_study=2,
        student_id="TP0112233",
        field_of_study="software engineer",
        progress="none",
    )

    mocker.patch.object(User, "login", return_value=mock_student)

    response = client.post(
        "/login",
        json={"email": "correctemail@gmail.com", "password": "123123123"},
    )

    assert response.status_code == 200
    print(response.json())
    assert response.json() == {
        "user": {
            "user_id": 1,
            "fullname": "fullname",
            "email": "Studentemail@email.email",
            "role": "student",
        },
        "university_mentor": {
            "user_id": 1,
            "fullname": "mentor1",
            "email": "email@email.email",
            "role": "universityMentor",
        },
        "year_of_study": 2,
        "field_of_study": "software engineer",
        "student_id": "TP0112233",
        "progress": "none",
    }


def test_login_blank_credential():
    response = client.post(
        "/login",
        json={"email": "", "password": ""},
    )

    assert response.status_code == 400
    assert response.json() == {"detail": "email and password are required."}

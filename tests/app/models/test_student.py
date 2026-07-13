from app.dependencies.dbExceptions import NotStudent
from app.models.Role import Role
from app.models.User import User, Student
import pytest


STUDENT_DATA = {
    "year_of_study": 2,
    "field_of_study": "software engineer",
    "student_id": "TP0112233",
    "university_mentor_id": 999,
    "progress": "none",
    "internship_start_date": None,
    "internship_duration_weeks": None,
}

MENTOR_DATA = {
    "user_id": 999,
    "fullname": "Mentor One",
    "email": "mentor@example.com",
    "role": Role.universityMentor,
}


def _mock_rows_from_query(connection, query):
    if "FROM student" in query:
        parts = query.split("FROM")[0].replace("SELECT", "").strip()
        columns = [c.strip() for c in parts.split(",")]
        return [tuple(STUDENT_DATA[c] for c in columns)]
    return []


def test_get_student_returns_student_for_student_role(mocker):
    user = User(
        fullname="John Doe", email="john@example.com", role=Role.student, user_id=1
    )
    mock_mentor = User(**MENTOR_DATA)
    mocker.patch(
        "app.dependencies.database_connector.execute_read",
        side_effect=_mock_rows_from_query,
    )
    mocker.patch.object(User, "getUserData", return_value=mock_mentor)

    result = Student.get_student(user)

    assert result.user.email == "john@example.com"
    assert result.university_mentor.email == "mentor@example.com"
    assert result.year_of_study == 2
    assert result.field_of_study == "software engineer"
    assert result.student_id == "TP0112233"
    assert result.progress == "none"


def test_get_student_raises_not_student_for_university_mentor(mocker):
    user = User(
        fullname="Jane Smith",
        email="jane@example.com",
        role=Role.universityMentor,
        user_id=2,
    )
    mock_mentor = User(**MENTOR_DATA)
    mocker.patch(
        "app.dependencies.database_connector.execute_read",
        side_effect=_mock_rows_from_query,
    )
    mocker.patch.object(User, "getUserData", return_value=mock_mentor)

    with pytest.raises(NotStudent):
        Student.get_student(user)


def test_get_student_raises_error_when_no_record_found(mocker):
    user = User(
        fullname="John Doe", email="john@example.com", role=Role.student, user_id=1
    )
    mocker.patch("app.dependencies.database_connector.execute_read", return_value=[])

    with pytest.raises(Exception):
        Student.get_student(user)

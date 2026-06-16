from app.dependencies.dbExceptions import IncorrectEmailOrPassword
from app.models.User import User
import pytest


def test_user_login(mocker):
    mock_user = [("mock", "mockmail@mail.com", "student", 1)]
    mock_student_data = [(2, "Computer Science", "TP12345", 999, "none")]
    mock_mentor_data = [("Mentor", "mentor@mail.com", "universityMentor", 999)]

    mocker.patch(
        "app.dependencies.database_connector.execute_read",
        side_effect=[mock_user, mock_student_data, mock_mentor_data],
    )

    assert (
        User.login("correctMail@mail.com", "correctPassword")
        != IncorrectEmailOrPassword
    )


def test_user_login_wrong_creds(mocker):
    mock_user = []
    mocker.patch(
        "app.dependencies.database_connector.execute_read", return_value=mock_user
    )
    with pytest.raises(IncorrectEmailOrPassword):
        User.login("wrongEmail@email.email", "wrongPassword")

from app.dependencies.dbExceptions import IncorrectEmailOrPassword
from app.models.User import User
import pytest


def test_user_login(mocker):
    mock_user = [("mock", "mockname", "mockmail@mail.com", "mockPass", "student")]
    mocker.patch(
        "app.dependencies.database_connector.execute_read", return_value=mock_user
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

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


def test_get_notifications_success(mocker):
    app.dependency_overrides[auth.get_current_user] = _override_user(mock_student_user)
    try:
        mocker.patch(
            "app.dependencies.database_connector.execute_read",
            return_value=[
                (1, 1, "msg 1", "type_a", 10, False, "2026-06-27 10:00:00"),
                (2, 1, "msg 2", "type_b", None, True, "2026-06-26 09:00:00"),
            ],
        )
        mocker.patch(
            "app.dependencies.database_connector.create_connection",
            return_value=None,
        )

        response = client.get("/notifications/")

        assert response.status_code == 200
        body = response.json()
        assert len(body) == 2
        assert body[0]["notification_id"] == 1
        assert body[0]["message"] == "msg 1"
        assert body[0]["is_read"] is False
        assert body[1]["notification_id"] == 2
        assert body[1]["is_read"] is True
        assert body[1]["related_id"] is None
    finally:
        app.dependency_overrides.clear()


def test_get_notifications_empty(mocker):
    app.dependency_overrides[auth.get_current_user] = _override_user(mock_student_user)
    try:
        mocker.patch(
            "app.dependencies.database_connector.execute_read",
            return_value=[],
        )
        mocker.patch(
            "app.dependencies.database_connector.create_connection",
            return_value=None,
        )

        response = client.get("/notifications/")

        assert response.status_code == 200
        assert response.json() == []
    finally:
        app.dependency_overrides.clear()


def test_get_notifications_not_authenticated():
    response = client.get("/notifications/")
    assert response.status_code == 401


def test_get_unread_count_success(mocker):
    app.dependency_overrides[auth.get_current_user] = _override_user(mock_mentor_user)
    try:
        mocker.patch(
            "app.dependencies.database_connector.execute_read",
            return_value=[(3,)],
        )
        mocker.patch(
            "app.dependencies.database_connector.create_connection",
            return_value=None,
        )

        response = client.get("/notifications/unread-count")

        assert response.status_code == 200
        assert response.json() == {"unread_count": 3}
    finally:
        app.dependency_overrides.clear()


def test_get_unread_count_zero(mocker):
    app.dependency_overrides[auth.get_current_user] = _override_user(mock_student_user)
    try:
        mocker.patch(
            "app.dependencies.database_connector.execute_read",
            return_value=[(0,)],
        )
        mocker.patch(
            "app.dependencies.database_connector.create_connection",
            return_value=None,
        )

        response = client.get("/notifications/unread-count")

        assert response.status_code == 200
        assert response.json() == {"unread_count": 0}
    finally:
        app.dependency_overrides.clear()


def test_get_unread_count_not_authenticated():
    response = client.get("/notifications/unread-count")
    assert response.status_code == 401


def test_mark_as_read_success(mocker):
    app.dependency_overrides[auth.get_current_user] = _override_user(mock_student_user)
    try:
        mock_write = mocker.patch("app.dependencies.database_connector.execute_write")
        mocker.patch(
            "app.dependencies.database_connector.create_connection",
            return_value=None,
        )

        response = client.patch("/notifications/5/read")

        assert response.status_code == 200
        assert response.json() == {"message": "Notification marked as read"}
        mock_write.assert_called_once()
        call_query = mock_write.call_args[0][1]
        assert "notification_id = 5" in call_query
    finally:
        app.dependency_overrides.clear()


def test_mark_as_read_not_authenticated():
    response = client.patch("/notifications/1/read")
    assert response.status_code == 401

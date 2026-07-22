from app.models.Notification import Notification


def test_create_notification(mocker):
    mock_write = mocker.patch("app.dependencies.database_connector.execute_write")
    mocker.patch("app.dependencies.database_connector.create_connection", return_value=None)
    mocker.patch("app.models.FcmToken.FcmToken.get_tokens", return_value=[])
    mocker.patch("app.models.Notification.send_push")

    Notification.create_notification(
        user_id=1,
        message="Test notification",
        type="test_type",
        related_id=42,
    )

    mock_write.assert_called_once()
    call_query = mock_write.call_args[0][1]
    assert "INSERT INTO notification" in call_query
    assert "1" in call_query
    assert "Test notification" in call_query
    assert "test_type" in call_query
    assert "42" in call_query


def test_create_notification_without_related_id(mocker):
    mock_write = mocker.patch("app.dependencies.database_connector.execute_write")
    mocker.patch("app.dependencies.database_connector.create_connection", return_value=None)
    mocker.patch("app.models.FcmToken.FcmToken.get_tokens", return_value=[])
    mocker.patch("app.models.Notification.send_push")

    Notification.create_notification(
        user_id=2,
        message="No related id",
        type="simple",
    )

    mock_write.assert_called_once()
    call_query = mock_write.call_args[0][1]
    assert "NULL" in call_query


def test_get_notifications(mocker):
    mock_read = mocker.patch(
        "app.dependencies.database_connector.execute_read",
        return_value=[
            (1, 1, "msg 1", "type_a", 10, False, "2026-06-27 10:00:00"),
            (2, 1, "msg 2", "type_b", None, True, "2026-06-26 09:00:00"),
        ],
    )
    mocker.patch("app.dependencies.database_connector.create_connection", return_value=None)

    results = Notification.get_notifications(1)

    assert len(results) == 2
    assert results[0].notification_id == 1
    assert results[0].user_id == 1
    assert results[0].message == "msg 1"
    assert results[0].type == "type_a"
    assert results[0].related_id == 10
    assert results[0].is_read is False
    assert results[0].created_at == "2026-06-27 10:00:00"
    assert results[1].notification_id == 2
    assert results[1].message == "msg 2"
    assert results[1].related_id is None
    assert results[1].is_read is True

    mock_read.assert_called_once()
    call_query = mock_read.call_args[0][1]
    assert "WHERE user_id = 1" in call_query
    assert "ORDER BY created_at DESC" in call_query


def test_get_notifications_returns_empty_list(mocker):
    mocker.patch("app.dependencies.database_connector.execute_read", return_value=[])
    mocker.patch("app.dependencies.database_connector.create_connection", return_value=None)

    results = Notification.get_notifications(1)
    assert results == []


def test_get_unread_count(mocker):
    mocker.patch(
        "app.dependencies.database_connector.execute_read",
        return_value=[(3,)],
    )
    mocker.patch("app.dependencies.database_connector.create_connection", return_value=None)

    count = Notification.get_unread_count(1)
    assert count == 3


def test_get_unread_count_zero(mocker):
    mocker.patch(
        "app.dependencies.database_connector.execute_read",
        return_value=[(0,)],
    )
    mocker.patch("app.dependencies.database_connector.create_connection", return_value=None)

    count = Notification.get_unread_count(1)
    assert count == 0


def test_mark_as_read(mocker):
    mock_write = mocker.patch("app.dependencies.database_connector.execute_write")
    mocker.patch("app.dependencies.database_connector.create_connection", return_value=None)

    Notification.mark_as_read(5)

    mock_write.assert_called_once()
    call_query = mock_write.call_args[0][1]
    assert "UPDATE notification" in call_query
    assert "is_read = true" in call_query
    assert "notification_id = 5" in call_query

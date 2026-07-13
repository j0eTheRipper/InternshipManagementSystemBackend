from app.models.Attendance import Attendance


def test_get_history_returns_records_ordered_desc(mocker):
    mock_rows = [
        (3, "TP0112233", "2025-07-10 09:00:00"),
        (2, "TP0112233", "2025-07-09 09:15:00"),
        (1, "TP0112233", "2025-07-08 08:45:00"),
    ]
    mocker.patch(
        "app.dependencies.database_connector.execute_read",
        return_value=mock_rows,
    )

    result = Attendance.get_history("TP0112233")

    assert len(result) == 3
    assert result[0].attendance_id == 3
    assert result[0].student_id == "TP0112233"
    assert result[0].checked_at == "2025-07-10 09:00:00"
    assert result[1].attendance_id == 2
    assert result[2].attendance_id == 1


def test_get_history_returns_empty_list_when_no_records(mocker):
    mocker.patch(
        "app.dependencies.database_connector.execute_read",
        return_value=[],
    )

    result = Attendance.get_history("TP9999999")

    assert result == []


def test_get_history_handles_none_checked_at(mocker):
    mock_rows = [
        (1, "TP0112233", None),
    ]
    mocker.patch(
        "app.dependencies.database_connector.execute_read",
        return_value=mock_rows,
    )

    result = Attendance.get_history("TP0112233")

    assert len(result) == 1
    assert result[0].checked_at is None


def test_record_returns_attendance_object(mocker):
    mock_insert_rows = []
    mock_select_rows = [(5, "2025-07-10 10:30:00")]

    mocker.patch(
        "app.dependencies.database_connector.execute_read",
        return_value=mock_select_rows,
    )
    mocker.patch(
        "app.dependencies.database_connector.execute_write",
    )

    result = Attendance.record("TP0112233")

    assert result is not None
    assert result.attendance_id == 5
    assert result.student_id == "TP0112233"
    assert result.checked_at == "2025-07-10 10:30:00"


def test_get_today_returns_record_when_checked_in(mocker):
    mock_rows = [(1, "TP0112233", "2025-07-10 09:00:00")]
    mocker.patch(
        "app.dependencies.database_connector.execute_read",
        return_value=mock_rows,
    )

    result = Attendance.get_today("TP0112233")

    assert result is not None
    assert result.attendance_id == 1
    assert result.checked_at == "2025-07-10 09:00:00"


def test_get_today_returns_none_when_not_checked_in(mocker):
    mocker.patch(
        "app.dependencies.database_connector.execute_read",
        return_value=[],
    )

    result = Attendance.get_today("TP0112233")

    assert result is None

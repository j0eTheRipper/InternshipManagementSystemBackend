from app.models.DailyTask import DailyTask


def test_submit_creates_new_daily_task(mocker):
    mocker.patch("app.dependencies.database_connector.execute_write")
    mocker.patch(
        "app.dependencies.database_connector.execute_read",
        return_value=[(1, "2025-07-10", "2025-07-07", "2025-07-13", "2025-07-10 10:00:00", False, None, None)],
    )

    result = DailyTask.submit("TP0112233", "Built auth flow", "2025-07-10", "2025-07-07", "2025-07-13")

    assert result is not None
    assert result.daily_task_id == 1
    assert result.student_id == "TP0112233"
    assert result.update_text == "Built auth flow"
    assert result.update_date == "2025-07-10"
    assert result.week_start_date == "2025-07-07"
    assert result.week_end_date == "2025-07-13"
    assert result.submitted_at == "2025-07-10 10:00:00"


def test_submit_updates_existing_daily_task(mocker):
    mocker.patch("app.dependencies.database_connector.execute_write")
    mocker.patch(
        "app.dependencies.database_connector.execute_read",
        return_value=[(1, "2025-07-11", "2025-07-07", "2025-07-13", "2025-07-11 09:00:00", False, None, None)],
    )

    result = DailyTask.submit("TP0112233", "Updated tasks", "2025-07-11", "2025-07-07", "2025-07-13")

    assert result is not None
    assert result.update_text == "Updated tasks"


def test_get_by_date_returns_task(mocker):
    mocker.patch(
        "app.dependencies.database_connector.execute_read",
        return_value=[(1, "TP0112233", "Built auth", "2025-07-10", "2025-07-07", "2025-07-13", "2025-07-10 10:00:00", False, None, None)],
    )

    result = DailyTask.get_by_date("TP0112233", "2025-07-10")

    assert result is not None
    assert result.update_text == "Built auth"
    assert result.update_date == "2025-07-10"


def test_get_by_date_returns_none_when_not_found(mocker):
    mocker.patch(
        "app.dependencies.database_connector.execute_read",
        return_value=[],
    )

    result = DailyTask.get_by_date("TP0112233", "2025-07-99")

    assert result is None


def test_get_history_returns_records_ordered_by_date_desc(mocker):
    mocker.patch(
        "app.dependencies.database_connector.execute_read",
        return_value=[
            (2, "TP0112233", "Day 2 tasks", "2025-07-11", "2025-07-07", "2025-07-13", "2025-07-11 10:00:00", False, None, None),
            (1, "TP0112233", "Day 1 tasks", "2025-07-10", "2025-07-07", "2025-07-13", "2025-07-10 10:00:00", False, None, None),
        ],
    )

    result = DailyTask.get_history("TP0112233")

    assert len(result) == 2
    assert result[0].update_date == "2025-07-11"
    assert result[1].update_date == "2025-07-10"


def test_get_history_returns_empty_list_when_no_records(mocker):
    mocker.patch(
        "app.dependencies.database_connector.execute_read",
        return_value=[],
    )

    result = DailyTask.get_history("TP9999999")

    assert result == []

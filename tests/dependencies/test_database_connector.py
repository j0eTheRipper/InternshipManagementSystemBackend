from unittest.mock import Mock, patch

from app.dependencies import database_connector


@patch("app.dependencies.database_connector.connect")
def test_db_connection_prod(mock_connect):
    connection = Mock()
    mock_connect.return_value = connection

    result = database_connector.create_connection(False)

    assert result is connection
    mock_connect.assert_called_once_with(
        database="internshipdb",
        user="postgres",
        password="hushhush",
        host="localhost",
        port="5432",
    )


@patch("app.dependencies.database_connector.connect")
def test_db_connection_test(mock_connect):
    connection = Mock()
    mock_connect.return_value = connection

    result = database_connector.create_connection()

    assert result is connection
    mock_connect.assert_called_once_with(
        database="internshipdb_test",
        user="postgres",
        password="hushhush",
        host="localhost",
        port="5432",
    )


def test_db_read_query():
    cursor = Mock()
    cursor.fetchall.return_value = [{"id": 1, "username": "jack"}]
    connection = Mock()
    connection.cursor.return_value = cursor
    query = "SELECT * FROM users"

    response = database_connector.execute_read(connection, query)

    assert response == [{"id": 1, "username": "jack"}]
    connection.cursor.assert_called_once_with()
    cursor.execute.assert_called_once_with(query)
    cursor.fetchall.assert_called_once_with()


def test_db_write_query():
    cursor = Mock()
    connection = Mock()
    connection.cursor.return_value = cursor
    query = """
        insert into users (username, fullname, password, email, role) values (
'jack', 'jackSparrow', '119911', 'jack@sparrow.sea', 'companyMentor'
)
    """

    database_connector.execute_write(connection, query)

    connection.cursor.assert_called_once_with()
    cursor.execute.assert_called_once_with(query)

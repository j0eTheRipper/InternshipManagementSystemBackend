from . import database_connector


def test_db_connection_prod():
    connection = database_connector.create_connection(False)

    assert connection is not None


def test_db_connection_test():
    connection = database_connector.create_connection()

    assert connection is not None


def test_db_read_query():
    connection = database_connector.create_connection()
    query = "SELECT * FROM users"

    response = database_connector.execute_read(connection, query)

    assert response is not None


def test_db_write_query():
    connection = database_connector.create_connection()
    query = """
        insert into users (username, fullname, password, email, role) values (
'jack', 'jackSparrow', '119911', 'jack@sparrow.sea', 'companyMentor'
)
    """
    database_connector.execute_write(connection, query)

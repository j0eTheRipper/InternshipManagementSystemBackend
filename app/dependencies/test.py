import database_connector


def test_db_connection_prod():
    connection = database_connector.create_connection(False)

    assert connection is not None

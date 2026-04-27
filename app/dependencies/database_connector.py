from psycopg2 import connect
from psycopg2 import OperationalError


def create_connection(test=True):
    connection = None
    try:
        connection = connect(
            database="internshipdb_test" if test else "internshipdb",
            user="postgres",
            password="hushhush",
            host="localhost",
            port="5432",
        )
    except OperationalError as e:
        print(f"error {e}")

    return connection


def execute_read(connection, query):
    cursor = connection.cursor()

    try:
        cursor.execute(query)
        return cursor.fetchall()
    except OperationalError as e:
        print(f"error {e}")


def execute_write(connection, query):
    cursor = connection.cursor()

    try:
        cursor.execute(query)
    except OperationalError as e:
        print(f"error {e}")

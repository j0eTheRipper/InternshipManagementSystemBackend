from psycopg2 import connect
from psycopg2 import OperationalError


def create_connection(test=True):
    connection = None
    try:
        connection = connect(
            database="internshipdb_test" if test else "internship_db",
            user="postgres",
            password="hushhush",
            host="localhost",
            port="5432",
        )
    except OperationalError as e:
        print(f"error {e}")

    return connection

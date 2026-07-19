from pydantic import BaseModel

from app.dependencies import database_connector


class FcmToken(BaseModel):
    id: int
    user_id: int
    token: str
    created_at: str | None = None

    @staticmethod
    def save(user_id: int, token: str):
        connection = database_connector.create_connection(False)
        existing = database_connector.execute_read(
            connection,
            f"SELECT id FROM fcm_token WHERE user_id = {user_id} AND token = '{token}';",
        )
        if existing:
            return
        database_connector.execute_write(
            connection,
            f"INSERT INTO fcm_token (user_id, token) VALUES ({user_id}, '{token}');",
        )

    @staticmethod
    def get_tokens(user_id: int) -> list[str]:
        connection = database_connector.create_connection(False)
        rows = database_connector.execute_read(
            connection,
            f"SELECT token FROM fcm_token WHERE user_id = {user_id};",
        )
        return [row[0] for row in rows] if rows else []

    @staticmethod
    def delete(token: str):
        connection = database_connector.create_connection(False)
        database_connector.execute_write(
            connection,
            f"DELETE FROM fcm_token WHERE token = '{token}';",
        )

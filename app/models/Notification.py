from pydantic import BaseModel

from app.dependencies import database_connector
from app.models.FcmToken import FcmToken
from app.services.firebase_service import send_push


class Notification(BaseModel):
    notification_id: int
    user_id: int
    message: str
    type: str
    related_id: int | None = None
    is_read: bool = False
    created_at: str | None = None

    @staticmethod
    def create_notification(
        user_id: int, message: str, type: str, related_id: int | None = None
    ):
        connection = database_connector.create_connection(False)
        related = str(related_id) if related_id is not None else "NULL"
        query = f"INSERT INTO notification (user_id, message, type, related_id) VALUES ({user_id}, '{message}', '{type}', {related});"
        database_connector.execute_write(connection, query)

        tokens = FcmToken.get_tokens(user_id)
        for token in tokens:
            send_push(token, "Internship Manager", message)

    @staticmethod
    def get_notifications(user_id: int):
        connection = database_connector.create_connection(False)
        query = f"SELECT notification_id, user_id, message, type, related_id, is_read, created_at FROM notification WHERE user_id = {user_id} ORDER BY created_at DESC;"
        notifications = database_connector.execute_read(connection, query)
        if not notifications:
            return []

        return [
            Notification(
                notification_id=notification[0],
                user_id=notification[1],
                message=notification[2],
                type=notification[3],
                related_id=notification[4],
                is_read=notification[5],
                created_at=str(notification[6]) if notification[6] else None,
            )
            for notification in notifications
        ]

    @staticmethod
    def get_unread_count(user_id: int) -> int:
        connection = database_connector.create_connection(False)
        query = f"SELECT COUNT(*) FROM notification WHERE user_id = {user_id} AND is_read = false;"
        results = database_connector.execute_read(connection, query)
        return results[0][0] if results else 0

    @staticmethod
    def mark_as_read(notification_id: int):
        connection = database_connector.create_connection(False)
        query = f"UPDATE notification SET is_read = true WHERE notification_id = {notification_id};"
        database_connector.execute_write(connection, query)

    @staticmethod
    def mark_read_by_type(user_id: int, type: str, related_id: int):
        connection = database_connector.create_connection(False)
        query = f"UPDATE notification SET is_read = true WHERE user_id = {user_id} AND type = '{type}' AND related_id = {related_id} AND is_read = false;"
        database_connector.execute_write(connection, query)

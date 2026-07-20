from pydantic import BaseModel

from app.dependencies import database_connector


class Message(BaseModel):
    message_id: int
    conversation_id: int
    sender_id: int
    content: str
    created_at: str | None = None
    is_read: bool = False

    @staticmethod
    def create_message(conversation_id: int, sender_id: int, content: str):
        connection = database_connector.create_connection(False)
        database_connector.execute_write(
            connection,
            f"INSERT INTO message (conversation_id, sender_id, content) VALUES ({conversation_id}, {sender_id}, '{content}');",
        )
        row = database_connector.execute_read(
            connection,
            f"SELECT message_id, created_at FROM message WHERE conversation_id = {conversation_id} ORDER BY created_at DESC LIMIT 1;",
        )
        return {
            "message_id": row[0][0],
            "conversation_id": conversation_id,
            "sender_id": sender_id,
            "content": content,
            "created_at": str(row[0][1]) if row[0][1] else None,
        }

    @staticmethod
    def get_messages(conversation_id: int, limit: int = 50, before: int | None = None):
        connection = database_connector.create_connection(False)
        before_clause = f"AND m.message_id < {before}" if before else ""
        rows = database_connector.execute_read(
            connection,
            f"""
            SELECT m.message_id, m.conversation_id, m.sender_id, m.content, m.created_at,
                   CASE WHEN mrr.message_id IS NOT NULL THEN true ELSE false END AS is_read
            FROM message m
            LEFT JOIN message_read_receipt mrr ON mrr.message_id = m.message_id AND mrr.user_id = m.sender_id
            WHERE m.conversation_id = {conversation_id} {before_clause}
            ORDER BY m.created_at DESC
            LIMIT {limit};
            """,
        )

        if not rows:
            return []

        return [
            {
                "message_id": r[0],
                "conversation_id": r[1],
                "sender_id": r[2],
                "content": r[3],
                "created_at": str(r[4]) if r[4] else None,
                "is_read": r[5],
            }
            for r in rows
        ]

    @staticmethod
    def get_last_message(conversation_id: int):
        connection = database_connector.create_connection(False)
        row = database_connector.execute_read(
            connection,
            f"SELECT message_id, conversation_id, sender_id, content, created_at FROM message WHERE conversation_id = {conversation_id} ORDER BY created_at DESC LIMIT 1;",
        )
        if not row:
            return None
        r = row[0]
        return {
            "message_id": r[0],
            "conversation_id": r[1],
            "sender_id": r[2],
            "content": r[3],
            "created_at": str(r[4]) if r[4] else None,
        }

    @staticmethod
    def mark_as_read(conversation_id: int, user_id: int):
        connection = database_connector.create_connection(False)
        database_connector.execute_write(
            connection,
            f"""
            INSERT INTO message_read_receipt (message_id, user_id)
            SELECT m.message_id, {user_id}
            FROM message m
            WHERE m.conversation_id = {conversation_id}
              AND m.sender_id != {user_id}
              AND NOT EXISTS (
                  SELECT 1 FROM message_read_receipt mrr
                  WHERE mrr.message_id = m.message_id AND mrr.user_id = {user_id}
              )
            ON CONFLICT (message_id, user_id) DO NOTHING;
            """,
        )

    @staticmethod
    def mark_single_as_read(message_id: int, user_id: int):
        connection = database_connector.create_connection(False)
        database_connector.execute_write(
            connection,
            f"""
            INSERT INTO message_read_receipt (message_id, user_id)
            VALUES ({message_id}, {user_id})
            ON CONFLICT (message_id, user_id) DO NOTHING;
            """,
        )

    @staticmethod
    def get_read_by(message_id: int):
        connection = database_connector.create_connection(False)
        rows = database_connector.execute_read(
            connection,
            f"SELECT user_id, read_at FROM message_read_receipt WHERE message_id = {message_id};",
        )
        if not rows:
            return []
        return [{"user_id": r[0], "read_at": str(r[1]) if r[1] else None} for r in rows]

    @staticmethod
    def get_unread_count(conversation_id: int, user_id: int) -> int:
        connection = database_connector.create_connection(False)
        row = database_connector.execute_read(
            connection,
            f"""
            SELECT COUNT(*)
            FROM message m
            WHERE m.conversation_id = {conversation_id}
              AND m.sender_id != {user_id}
              AND NOT EXISTS (
                  SELECT 1 FROM message_read_receipt mrr
                  WHERE mrr.message_id = m.message_id AND mrr.user_id = {user_id}
              );
            """,
        )
        return row[0][0] if row else 0

    @staticmethod
    def get_total_unread(user_id: int) -> int:
        connection = database_connector.create_connection(False)
        row = database_connector.execute_read(
            connection,
            f"""
            SELECT COUNT(*)
            FROM message m
            JOIN conversation c ON c.conversation_id = m.conversation_id
            WHERE (c.user1_id = {user_id} OR c.user2_id = {user_id})
              AND m.sender_id != {user_id}
              AND NOT EXISTS (
                  SELECT 1 FROM message_read_receipt mrr
                  WHERE mrr.message_id = m.message_id AND mrr.user_id = {user_id}
              );
            """,
        )
        return row[0][0] if row else 0

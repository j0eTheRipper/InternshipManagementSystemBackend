from pydantic import BaseModel

from app.dependencies import database_connector


class Conversation(BaseModel):
    conversation_id: int
    user1_id: int
    user2_id: int
    created_at: str | None = None

    @staticmethod
    def get_or_create(user1_id: int, user2_id: int):
        if user1_id == user2_id:
            return None

        a, b = (user1_id, user2_id) if user1_id < user2_id else (user2_id, user1_id)

        connection = database_connector.create_connection(False)
        row = database_connector.execute_read(
            connection,
            f"SELECT conversation_id FROM conversation WHERE user1_id = {a} AND user2_id = {b};",
        )

        if row:
            return row[0][0]

        database_connector.execute_write(
            connection,
            f"INSERT INTO conversation (user1_id, user2_id) VALUES ({a}, {b});",
        )

        row = database_connector.execute_read(
            connection,
            f"SELECT conversation_id FROM conversation WHERE user1_id = {a} AND user2_id = {b};",
        )
        return row[0][0]

    @staticmethod
    def get_user_conversations(user_id: int):
        connection = database_connector.create_connection(False)
        rows = database_connector.execute_read(
            connection,
            f"""
            SELECT
                c.conversation_id,
                CASE WHEN c.user1_id = {user_id} THEN c.user2_id ELSE c.user1_id END AS other_user_id,
                u.fullname,
                u.role,
                m.content AS last_message,
                m.created_at AS last_message_at,
                m.sender_id AS last_sender_id,
                (
                    SELECT COUNT(*)
                    FROM message msg
                    WHERE msg.conversation_id = c.conversation_id
                      AND msg.sender_id != {user_id}
                      AND NOT EXISTS (
                          SELECT 1 FROM message_read_receipt mrr
                          WHERE mrr.message_id = msg.message_id AND mrr.user_id = {user_id}
                      )
                ) AS unread_count
            FROM conversation c
            JOIN users u ON u.id = CASE WHEN c.user1_id = {user_id} THEN c.user2_id ELSE c.user1_id END
            LEFT JOIN message m ON m.conversation_id = c.conversation_id
                AND m.created_at = (
                    SELECT MAX(m2.created_at)
                    FROM message m2
                    WHERE m2.conversation_id = c.conversation_id
                )
            WHERE c.user1_id = {user_id} OR c.user2_id = {user_id}
            ORDER BY COALESCE(m.created_at, c.created_at) DESC;
            """,
        )

        if not rows:
            return []

        return [
            {
                "conversation_id": r[0],
                "other_user_id": r[1],
                "other_user_name": r[2],
                "other_user_role": r[3],
                "last_message": r[4],
                "last_message_at": str(r[5]) if r[5] else None,
                "last_sender_id": r[6],
                "unread_count": r[7],
            }
            for r in rows
        ]

    @staticmethod
    def get_conversation(conversation_id: int):
        connection = database_connector.create_connection(False)
        row = database_connector.execute_read(
            connection,
            f"SELECT conversation_id, user1_id, user2_id, created_at FROM conversation WHERE conversation_id = {conversation_id};",
        )
        if not row:
            return None
        r = row[0]
        return {
            "conversation_id": r[0],
            "user1_id": r[1],
            "user2_id": r[2],
            "created_at": str(r[3]) if r[3] else None,
        }

    @staticmethod
    def is_participant(conversation_id: int, user_id: int) -> bool:
        conv = Conversation.get_conversation(conversation_id)
        if not conv:
            return False
        return user_id in (conv["user1_id"], conv["user2_id"])

    @staticmethod
    def get_other_participant(conversation_id: int, user_id: int) -> int | None:
        conv = Conversation.get_conversation(conversation_id)
        if not conv:
            return None
        if user_id == conv["user1_id"]:
            return conv["user2_id"]
        if user_id == conv["user2_id"]:
            return conv["user1_id"]
        return None

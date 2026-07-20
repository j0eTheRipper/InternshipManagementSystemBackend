from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, WebSocket, WebSocketDisconnect, Query
from pydantic import BaseModel
import jwt

from app.dependencies.auth import get_current_user, SECRET_KEY, ALGORITHM
from app.dependencies.chat_auth import can_chat
from app.dependencies import database_connector
from app.models.User import User, Student
from app.models.Role import Role
from app.models.Conversation import Conversation
from app.models.Message import Message
from app.models.Notification import Notification
from app.models.FcmToken import FcmToken
from app.services.firebase_service import send_push
from app.services.connection_manager import manager

router = APIRouter(prefix="/chat")


class CreateConversationRequest(BaseModel):
    user_id: int


class SendMessageRequest(BaseModel):
    content: str


@router.get("/conversations")
async def get_conversations(user: Annotated[User, Depends(get_current_user)]):
    conversations = Conversation.get_user_conversations(user.user_id)
    return {"conversations": conversations}


@router.post("/conversations")
async def get_or_create_conversation(
    body: CreateConversationRequest,
    user: Annotated[User, Depends(get_current_user)],
):
    if not can_chat(user.user_id, body.user_id):
        raise HTTPException(403, "You are not allowed to chat with this user")

    conversation_id = Conversation.get_or_create(user.user_id, body.user_id)
    if conversation_id is None:
        raise HTTPException(400, "Cannot create conversation with yourself")

    return {"conversation_id": conversation_id}


@router.get("/conversations/{conversation_id}/messages")
async def get_messages(
    conversation_id: int,
    before: int | None = None,
    user: Annotated[User, Depends(get_current_user)] = None,
):
    if not Conversation.is_participant(conversation_id, user.user_id):
        raise HTTPException(403, "You are not a participant of this conversation")

    messages = Message.get_messages(conversation_id, limit=50, before=before)
    return {"messages": messages}


@router.post("/conversations/{conversation_id}/messages")
async def send_message_rest(
    conversation_id: int,
    body: SendMessageRequest,
    user: Annotated[User, Depends(get_current_user)],
):
    if not Conversation.is_participant(conversation_id, user.user_id):
        raise HTTPException(403, "You are not a participant of this conversation")

    if not body.content.strip():
        raise HTTPException(400, "Message content cannot be empty")

    msg = Message.create_message(conversation_id, user.user_id, body.content.strip())

    other_id = Conversation.get_other_participant(conversation_id, user.user_id)
    if other_id and manager.is_online(other_id):
        await manager.send_to_user(other_id, {
            "type": "message",
            "message_id": msg["message_id"],
            "sender_id": msg["sender_id"],
            "content": msg["content"],
            "created_at": msg["created_at"],
        })
    elif other_id:
        sender = User.getUserData(user.user_id)
        Notification.create_notification(
            other_id,
            f"New message from {sender.fullname}",
            "new_message",
            conversation_id,
        )

    return msg


@router.get("/unread-total")
async def get_unread_total(user: Annotated[User, Depends(get_current_user)]):
    count = Message.get_total_unread(user.user_id)
    return {"unread_count": count}


@router.get("/contacts")
async def get_contacts(user: Annotated[User, Depends(get_current_user)]):
    contacts = []
    connection = database_connector.create_connection(False)

    if user.role == Role.admin:
        rows = database_connector.execute_read(
            connection,
            "SELECT id, fullname, email, role FROM users WHERE role != 'admin' AND role != 'headhunter' ORDER BY fullname;",
        )
        if rows:
            for r in rows:
                contacts.append({"user_id": r[0], "fullname": r[1], "email": r[2], "role": r[3]})

    elif user.role == Role.student:
        row = database_connector.execute_read(
            connection,
            f"SELECT university_mentor_id, company_supervisor_id FROM student WHERE user_id = {user.user_id};",
        )
        if row:
            mentor_id = row[0][0]
            supervisor_id = row[0][1]
            ids = [mentor_id]
            if supervisor_id is not None:
                ids.append(supervisor_id)
            placeholders = ','.join(str(i) for i in ids)
            rows = database_connector.execute_read(
                connection,
                f"SELECT id, fullname, email, role FROM users WHERE id IN ({placeholders});",
            )
            if rows:
                for r in rows:
                    contacts.append({"user_id": r[0], "fullname": r[1], "email": r[2], "role": r[3]})

    elif user.role == Role.universityMentor:
        rows = database_connector.execute_read(
            connection,
            f"SELECT user_id, company_supervisor_id FROM student WHERE university_mentor_id = {user.user_id};",
        )
        if rows:
            ids = set()
            for r in rows:
                ids.add(r[0])
                if r[1] is not None:
                    ids.add(r[1])
            if ids:
                placeholders = ','.join(str(i) for i in ids)
                user_rows = database_connector.execute_read(
                    connection,
                    f"SELECT id, fullname, email, role FROM users WHERE id IN ({placeholders});",
                )
                if user_rows:
                    for r in user_rows:
                        contacts.append({"user_id": r[0], "fullname": r[1], "email": r[2], "role": r[3]})

    elif user.role == Role.companySupervisor:
        rows = database_connector.execute_read(
            connection,
            f"SELECT user_id, university_mentor_id FROM student WHERE company_supervisor_id = {user.user_id};",
        )
        if rows:
            ids = set()
            for r in rows:
                ids.add(r[0])
                if r[1] is not None:
                    ids.add(r[1])
            if ids:
                placeholders = ','.join(str(i) for i in ids)
                user_rows = database_connector.execute_read(
                    connection,
                    f"SELECT id, fullname, email, role FROM users WHERE id IN ({placeholders});",
                )
                if user_rows:
                    for r in user_rows:
                        contacts.append({"user_id": r[0], "fullname": r[1], "email": r[2], "role": r[3]})

    return {"contacts": contacts}


@router.patch("/conversations/{conversation_id}/read")
async def mark_conversation_read(
    conversation_id: int,
    user: Annotated[User, Depends(get_current_user)],
):
    if not Conversation.is_participant(conversation_id, user.user_id):
        raise HTTPException(403, "You are not a participant of this conversation")

    Message.mark_as_read(conversation_id, user.user_id)

    Notification.mark_read_by_type(user.user_id, "new_message", conversation_id)

    other_id = Conversation.get_other_participant(conversation_id, user.user_id)
    if other_id and manager.is_online(other_id):
        await manager.send_to_user(other_id, {
            "type": "read",
            "user_id": user.user_id,
            "conversation_id": conversation_id,
        })

    return {"message": "Marked as read"}


async def chat_websocket(websocket: WebSocket, conversation_id: int, token: str = Query(...)):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id = int(payload.get("sub"))
    except (jwt.PyJWTError, ValueError, TypeError):
        await websocket.close(code=4001, reason="Invalid token")
        return

    if not Conversation.is_participant(conversation_id, user_id):
        await websocket.close(code=4003, reason="Not a participant")
        return

    await manager.connect(user_id, websocket)

    other_id = Conversation.get_other_participant(conversation_id, user_id)
    if other_id:
        await manager.send_to_user(other_id, {
            "type": "online_status",
            "user_id": user_id,
            "is_online": True,
        })

    try:
        while True:
            data = await websocket.receive_json()
            msg_type = data.get("type")

            if msg_type == "message":
                content = data.get("content", "").strip()
                if not content:
                    continue

                msg = Message.create_message(conversation_id, user_id, content)

                await websocket.send_json({
                    "type": "message",
                    "message_id": msg["message_id"],
                    "sender_id": msg["sender_id"],
                    "content": msg["content"],
                    "created_at": msg["created_at"],
                    "delivered": True,
                })

                if other_id and manager.is_online(other_id):
                    await manager.send_to_user(other_id, {
                        "type": "message",
                        "message_id": msg["message_id"],
                        "sender_id": msg["sender_id"],
                        "content": msg["content"],
                        "created_at": msg["created_at"],
                    })
                elif other_id:
                    sender = User.getUserData(user_id)
                    Notification.create_notification(
                        other_id,
                        f"New message from {sender.fullname}",
                        "new_message",
                        conversation_id,
                    )

            elif msg_type == "typing":
                if other_id and manager.is_online(other_id):
                    await manager.send_to_user(other_id, {
                        "type": "typing",
                        "user_id": user_id,
                        "is_typing": data.get("is_typing", False),
                    })

            elif msg_type == "read":
                message_id = data.get("message_id")
                if message_id:
                    Message.mark_as_read(conversation_id, user_id)
                    if other_id and manager.is_online(other_id):
                        await manager.send_to_user(other_id, {
                            "type": "read",
                            "user_id": user_id,
                            "conversation_id": conversation_id,
                            "message_id": message_id,
                        })

    except WebSocketDisconnect:
        pass
    finally:
        manager.disconnect(user_id, websocket)
        if other_id:
            await manager.send_to_user(other_id, {
                "type": "online_status",
                "user_id": user_id,
                "is_online": False,
            })

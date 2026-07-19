import os
import logging

import firebase_admin
from firebase_admin import credentials, messaging

logger = logging.getLogger(__name__)

_initialized = False


def init_firebase():
    global _initialized
    if _initialized:
        return
    service_account_path = os.path.join(
        os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
        "serviceAccountKey.json",
    )
    if not os.path.exists(service_account_path):
        logger.warning("serviceAccountKey.json not found — push notifications disabled")
        return
    cred = credentials.Certificate(service_account_path)
    firebase_admin.initialize_app(cred)
    _initialized = True
    logger.info("Firebase Admin SDK initialized")


def send_push(token: str, title: str, body: str):
    if not _initialized:
        return
    try:
        message = messaging.Message(
            notification=messaging.Notification(title=title, body=body),
            token=token,
        )
        messaging.send(message)
    except Exception as e:
        logger.warning(f"Failed to send push notification: {e}")

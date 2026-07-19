import logging
from datetime import datetime

from apscheduler.schedulers.background import BackgroundScheduler

from app.dependencies import database_connector
from app.models.FcmToken import FcmToken
from app.services.firebase_service import send_push

logger = logging.getLogger(__name__)

scheduler = BackgroundScheduler()


def _send_check_in_reminders():
    logger.info("Running daily check-in reminder job")
    connection = database_connector.create_connection(False)
    rows = database_connector.execute_read(
        connection,
        "SELECT user_id FROM student WHERE progress = 'accepted';",
    )
    if not rows:
        return
    count = 0
    for row in rows:
        user_id = row[0]
        tokens = FcmToken.get_tokens(user_id)
        for token in tokens:
            send_push(
                token,
                "Daily Check-in Reminder",
                "Don't forget to check in for today!",
            )
            count += 1
    logger.info(f"Sent {count} check-in reminders")


def start_scheduler():
    scheduler.add_job(
        _send_check_in_reminders,
        "cron",
        hour=9,
        minute=0,
        id="daily_check_in_reminder",
    )
    scheduler.start()
    logger.info("Scheduler started — daily check-in reminder at 09:00")

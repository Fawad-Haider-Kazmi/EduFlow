"""
EduFlow — Twilio WhatsApp Service.
Sends and queues WhatsApp messages via the Twilio API.
Falls back to console logging when credentials are absent (demo / local dev).
"""

import logging
from config import settings

logger = logging.getLogger(__name__)


def _get_client():
    if not settings.TWILIO_ACCOUNT_SID or not settings.TWILIO_AUTH_TOKEN:
        return None
    from twilio.rest import Client
    return Client(settings.TWILIO_ACCOUNT_SID, settings.TWILIO_AUTH_TOKEN)


async def send_whatsapp(to_number: str, message: str) -> bool:
    """
    Sends a WhatsApp message. to_number should be in E.164 format, e.g. +923001234567.
    Returns True on success, False on failure.
    """
    client = _get_client()
    if not client:
        logger.info(f"[WHATSAPP MOCK] To: {to_number}\n{message}")
        return True

    try:
        msg = client.messages.create(
            from_=settings.TWILIO_WHATSAPP_NUMBER,
            to=f"whatsapp:{to_number}",
            body=message,
        )
        logger.info(f"WhatsApp sent: SID={msg.sid} to={to_number}")
        return True
    except Exception as e:
        logger.error(f"WhatsApp send failed to {to_number}: {e}")
        return False


async def forward_parent_reply(student_name: str, teacher_email: str, reply_text: str) -> None:
    """
    Parent replies are NOT handled autonomously — they are forwarded to the teacher dashboard.
    This function logs the event; the dashboard polling picks it up from DB.
    """
    logger.info(
        f"[PARENT REPLY] Student: {student_name} | Teacher: {teacher_email} | "
        f"Reply: {reply_text}"
    )

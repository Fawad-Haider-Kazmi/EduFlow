"""
Telegram Bot notification service — replaces Twilio WhatsApp.
Free, no approval needed, works instantly with a bot token.

Setup:
  1. Message @BotFather on Telegram → /newbot → get BOT_TOKEN
  2. Set TELEGRAM_BOT_TOKEN in .env
  3. Users must start a chat with the bot first to get their chat_id
"""
import logging
from typing import Optional
import httpx
from config import settings

logger = logging.getLogger(__name__)


async def send_message(chat_id: str, text: str, parse_mode: str = "HTML") -> bool:
    """Send a Telegram message. Returns True on success."""
    if settings.DEMO_MODE:
        logger.info(f"[TELEGRAM DEMO] → {chat_id}: {text[:80]}...")
        return True

    token = getattr(settings, "TELEGRAM_BOT_TOKEN", "")
    if not token:
        logger.warning("TELEGRAM_BOT_TOKEN not set — skipping notification")
        return False

    url = f"https://api.telegram.org/bot{token}/sendMessage"
    try:
        async with httpx.AsyncClient(timeout=10) as client:
            resp = await client.post(url, json={
                "chat_id": chat_id,
                "text": text,
                "parse_mode": parse_mode,
            })
            if not resp.is_success:
                logger.warning(f"Telegram API error: {resp.status_code} {resp.text}")
            return resp.is_success
    except Exception as e:
        logger.error(f"Telegram send failed: {e}")
        return False


async def notify_parent_result(
    chat_id: str,
    student_name: str,
    assignment_title: str,
    score_str: str,
    strength: str,
    improvement: str,
    next_assessment: str,
) -> bool:
    """Waalid Agent — send grading summary to parent."""
    msg = (
        f"<b>EduFlow Report</b>\n"
        f"Student: <b>{student_name}</b>\n"
        f"Assignment: {assignment_title}\n"
        f"Score: <b>{score_str}</b>\n\n"
        f"Strength: {strength}\n"
        f"Work on: {improvement}\n"
        f"Next assessment: {next_assessment}"
    )
    return await send_message(chat_id, msg)


async def notify_dropout_risk(
    chat_id: str,
    student_name: str,
    scheme: str = "Ehsaas Wazaifa",
    helpline: str = "0800-26477",
) -> bool:
    """Waalid Agent — dropout risk alert to parent."""
    msg = (
        f"<b>EduFlow Alert</b>\n"
        f"{student_name} may need extra support to stay in school.\n\n"
        f"<b>{scheme}</b> can help — Helpline: {helpline}\n"
        f"Please speak with the class teacher."
    )
    return await send_message(chat_id, msg)


async def send_taleem_task(
    chat_id: str,
    student_name: str,
    day: int,
    tasks: list[str],
) -> bool:
    """Taleem Gap Agent — daily recovery task delivery."""
    task_lines = "\n".join(f"{i+1}. {t}" for i, t in enumerate(tasks))
    msg = (
        f"<b>Day {day}/14</b> — {student_name}\n\n"
        f"{task_lines}\n\n"
        f"Reply <b>DONE</b> when finished."
    )
    return await send_message(chat_id, msg)


async def notify_ghost_school_admin(
    chat_id: str,
    school_name: str,
    weeks_silent: int,
) -> bool:
    """Ghost School Detector — alert school admin."""
    msg = (
        f"<b>EduFlow School Alert</b>\n"
        f"{school_name} has had no student submissions for <b>{weeks_silent} weeks</b>.\n\n"
        f"Please submit at least one assignment within 48 hours or this will be escalated to the District Education Officer."
    )
    return await send_message(chat_id, msg)


async def notify_deo_escalation(
    chat_id: str,
    school_name: str,
    district: str,
    weeks_silent: int,
) -> bool:
    """Ghost School Detector — escalate to DEO after 48h admin non-response."""
    msg = (
        f"<b>EduFlow DEO Escalation</b>\n"
        f"School: <b>{school_name}</b> ({district})\n"
        f"Silent for: {weeks_silent} weeks\n"
        f"Admin did not respond within 48 hours.\n\n"
        f"Please conduct a physical verification visit."
    )
    return await send_message(chat_id, msg)

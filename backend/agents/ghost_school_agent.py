"""
AGENT 9 — Ghost School Detector Agent
Daily cron job. Monitors submission patterns across all registered schools.
Strict 2-step escalation: school admin first, then DEO after 48h non-response.
"""

import logging
from datetime import datetime, timedelta
from typing import Any

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from config import settings
from services.telegram_service import notify_ghost_school_admin, notify_deo_escalation

logger = logging.getLogger(__name__)

DEMO_ALERTS = [
    {
        "school_name": "Quetta Secondary School",
        "district": "Quetta",
        "province": "Balochistan",
        "flag_type": "ghost_school",
        "weeks_silent": 3,
        "last_submission_date": "2026-04-23",
        "escalation_step": 1,
        "admin_notified": True,
        "deo_escalated": False,
    }
]


async def run(db: AsyncSession) -> list[dict[str, Any]]:
    """
    Runs all 4 Ghost School Detection Rules and returns list of flagged schools.
    Must be called from the daily cron job, not per-submission.
    """
    if settings.DEMO_MODE:
        return DEMO_ALERTS

    from database import School, Submission, GhostSchoolAlert

    now = datetime.utcnow()
    three_weeks_ago = now - timedelta(weeks=3)
    four_weeks_ago = now - timedelta(weeks=4)

    # Load all schools registered > 4 weeks ago (Rule 1 baseline)
    schools_result = await db.execute(
        select(School).where(School.registered_at < four_weeks_ago, School.is_active == True)
    )
    schools = schools_result.scalars().all()

    alerts = []
    for school in schools:
        # ── Rule 2: Silence detection ─────────────────────────────────────────
        last_sub_result = await db.execute(
            select(func.max(Submission.submitted_at))
            .join(Submission.student)
            .where(Submission.student.has(school_id=school.id))
        )
        last_sub_date = last_sub_result.scalar()

        if last_sub_date and last_sub_date < three_weeks_ago:
            weeks_silent = int((now - last_sub_date).days / 7)
            alert = await _handle_alert(
                db, school, "ghost_school", weeks_silent, last_sub_date, now
            )
            if alert:
                alerts.append(alert)
            continue

        # ── Rule 4: Sudden drop ───────────────────────────────────────────────
        recent_count = await _weekly_count(db, school.id, now - timedelta(weeks=1), now)
        avg_4wk = await _avg_weekly_count(db, school.id, four_weeks_ago, now)
        if avg_4wk > 0 and recent_count / avg_4wk < 0.30:
            alert = await _handle_alert(
                db, school, "school_disruption", 0, last_sub_date, now
            )
            if alert:
                alerts.append(alert)

    return alerts


async def _handle_alert(
    db: AsyncSession,
    school: Any,
    flag_type: str,
    weeks_silent: int,
    last_submission_date: Any,
    now: datetime,
) -> dict | None:
    from database import GhostSchoolAlert

    # Check for existing open alert
    existing_result = await db.execute(
        select(GhostSchoolAlert).where(
            GhostSchoolAlert.school_id == school.id,
            GhostSchoolAlert.resolved == False,
        )
    )
    existing = existing_result.scalar_one_or_none()

    if existing:
        # Check if 48h has passed since admin was notified with no response
        if (
            existing.admin_notified
            and not existing.admin_response
            and not existing.deo_escalated
            and existing.admin_notified_at
            and (now - existing.admin_notified_at) > timedelta(hours=48)
        ):
            existing.escalation_step = 2
            existing.deo_escalated = True
            existing.deo_escalated_at = now
            logger.info(f"Escalating {school.name} to DEO (48h no response)")
        return _alert_to_dict(existing, school)

    # New alert — notify school admin (Step 1)
    admin_msg = (
        f"EduFlow Alert: No submissions recorded from {school.name} for {weeks_silent} week(s). "
        f"Please confirm all is well or update submission status within 48 hours. "
        f"Reply to this message or log in at app.eduflow.pk"
    )
    if school.admin_email:
        logger.info(f"[GHOST SCHOOL ALERT] To: {school.admin_email}\n{admin_msg}")
    # Send via Telegram if admin has a chat_id stored
    await notify_ghost_school_admin(
        chat_id=getattr(school, "admin_telegram_id", "") or school.admin_email or "",
        school_name=school.name,
        weeks_silent=weeks_silent,
    )

    new_alert = GhostSchoolAlert(
        school_id=school.id,
        flag_type=flag_type,
        weeks_silent=weeks_silent,
        last_submission_date=last_submission_date,
        escalation_step=1,
        admin_notified=True,
        admin_notified_at=now,
    )
    db.add(new_alert)
    await db.commit()
    await db.refresh(new_alert)

    return {
        "school_name": school.name,
        "district": school.district,
        "flag_type": flag_type,
        "weeks_silent": weeks_silent,
        "last_submission_date": str(last_submission_date)[:10] if last_submission_date else None,
        "escalation_step": 1,
        "admin_notified": True,
        "deo_escalated": False,
    }


async def _weekly_count(db: AsyncSession, school_id: Any, start: datetime, end: datetime) -> int:
    from database import Submission, Student
    result = await db.execute(
        select(func.count(Submission.id))
        .join(Submission.student)
        .where(Student.school_id == school_id, Submission.submitted_at.between(start, end))
    )
    return result.scalar() or 0


async def _avg_weekly_count(db: AsyncSession, school_id: Any, start: datetime, end: datetime) -> float:
    total = await _weekly_count(db, school_id, start, end)
    weeks = max((end - start).days / 7, 1)
    return total / weeks


def _alert_to_dict(alert: Any, school: Any) -> dict:
    return {
        "school_name": school.name,
        "district": school.district,
        "flag_type": alert.flag_type,
        "weeks_silent": alert.weeks_silent,
        "last_submission_date": str(alert.last_submission_date)[:10] if alert.last_submission_date else None,
        "escalation_step": alert.escalation_step,
        "admin_notified": alert.admin_notified,
        "deo_escalated": alert.deo_escalated,
    }

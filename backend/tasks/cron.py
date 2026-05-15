"""
EduFlow — Daily Cron Job
Runs Ghost School Detector every day at 2:00 AM (server local time).
Also sends 24h HITL reminder to teachers who haven't reviewed yet.
"""

import asyncio
import logging
from datetime import datetime, timedelta

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from database import AsyncSessionLocal, ReviewCheckpoint, Submission, Student, Teacher

logger = logging.getLogger(__name__)


async def run_ghost_school_check():
    """Daily job: detect ghost schools and escalate."""
    logger.info("Cron: Ghost School Detector starting...")
    async with AsyncSessionLocal() as db:
        import agents.ghost_school_agent as ghost
        alerts = await ghost.run(db)
        logger.info(f"Cron: Ghost School Detector found {len(alerts)} alert(s).")


async def run_hitl_reminders():
    """Hourly job: remind teachers about reviews that are due within 2 hours."""
    logger.info("Cron: Checking HITL reminder deadlines...")
    async with AsyncSessionLocal() as db:
        now = datetime.utcnow()
        remind_before = now + timedelta(hours=2)

        result = await db.execute(
            select(ReviewCheckpoint, Submission, Student, Teacher)
            .join(Submission, ReviewCheckpoint.submission_id == Submission.id)
            .join(Student, Submission.student_id == Student.id)
            .join(Teacher, Student.teacher_id == Teacher.id)
            .where(
                ReviewCheckpoint.status == "pending",
                ReviewCheckpoint.reminder_sent == False,
                ReviewCheckpoint.deadline <= remind_before,
            )
        )
        rows = result.all()
        for review, submission, student, teacher in rows:
            logger.info(
                f"Reminder: Submission {submission.id} for {student.name} "
                f"awaiting review by {teacher.name} ({teacher.email}). "
                f"Deadline: {review.deadline}"
            )
            # In production: send email or WhatsApp to teacher
            review.reminder_sent = True

        if rows:
            await db.commit()
        logger.info(f"Cron: Sent {len(rows)} reminder(s).")


def start_scheduler() -> AsyncIOScheduler:
    scheduler = AsyncIOScheduler()
    scheduler.add_job(run_ghost_school_check, "cron", hour=2, minute=0, id="ghost_school_daily")
    scheduler.add_job(run_hitl_reminders, "interval", hours=1, id="hitl_reminder_hourly")
    scheduler.start()
    logger.info("APScheduler started: ghost school daily @ 02:00, HITL reminders hourly.")
    return scheduler

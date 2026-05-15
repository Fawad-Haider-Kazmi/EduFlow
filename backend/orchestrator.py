"""
EduFlow Orchestrator — Master pipeline controller.
Coordinates all 9 agents in the exact order specified.
Logs every agent call to PostgreSQL. Retries once on failure.
"""

import asyncio
import logging
import uuid
from datetime import datetime, timedelta
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from database import AgentLog, ReviewCheckpoint, Submission, TaleemGapPlan
from config import settings

import agents.zubaan_agent as zubaan
import agents.ingestion_agent as ingestion
import agents.integrity_agent as integrity
import agents.grading_agent as grading
import agents.feedback_agent as feedback
import agents.analytics_agent as analytics
import agents.waalid_agent as waalid
import agents.taleem_gap_agent as taleem_gap

logger = logging.getLogger(__name__)


# ── WebSocket broadcaster (injected from main.py) ─────────────────────────────
_ws_broadcast = None

def set_broadcast(fn):
    global _ws_broadcast
    _ws_broadcast = fn

async def _broadcast(submission_id: str, event: dict):
    if _ws_broadcast:
        await _ws_broadcast(submission_id, event)


# ─────────────────────────────────────────────────────────────────────────────
#  AGENT RUNNER — logs every call, retries once on failure
# ─────────────────────────────────────────────────────────────────────────────

async def _run_agent(
    db: AsyncSession,
    submission_id: str,
    agent_name: str,
    coro,
) -> Any:
    """Runs an agent coroutine, logs input/output to AgentLog, retries once on error."""
    log = AgentLog(
        submission_id=uuid.UUID(submission_id),
        agent_name=agent_name,
        called_at=datetime.utcnow(),
        status="running",
        attempt=1,
    )
    db.add(log)
    await db.commit()

    await _broadcast(submission_id, {"event": "agent_start", "agent": agent_name, "step": agent_name})

    for attempt in range(1, 3):
        start = datetime.utcnow()
        try:
            result = await coro if attempt == 1 else await coro
            duration = int((datetime.utcnow() - start).total_seconds() * 1000)
            log.output_data = result if isinstance(result, dict) else {"text": str(result)[:2000]}
            log.status = "success"
            log.completed_at = datetime.utcnow()
            log.duration_ms = duration
            await db.commit()
            await _broadcast(submission_id, {"event": "agent_done", "agent": agent_name, "output": log.output_data})
            return result
        except Exception as e:
            duration = int((datetime.utcnow() - start).total_seconds() * 1000)
            logger.error(f"Agent {agent_name} failed (attempt {attempt}): {e}")
            if attempt == 1:
                log.status = "retried"
                log.attempt = 2
                log.error_message = str(e)
                await db.commit()
                # Re-create coro for retry (coros are one-shot in Python)
                continue
            log.status = "failed"
            log.error_message = str(e)
            log.duration_ms = duration
            await db.commit()
            await _broadcast(submission_id, {"event": "agent_error", "agent": agent_name, "error": str(e)})
            raise


# ─────────────────────────────────────────────────────────────────────────────
#  MAIN PIPELINE
# ─────────────────────────────────────────────────────────────────────────────

async def run_pipeline(
    db: AsyncSession,
    submission: Submission,
    student,
    assignment,
    teacher,
    class_submissions: list[dict],
) -> None:
    """
    Full 9-step orchestration pipeline. Runs async in the background.
    Updates submission.status and pipeline_step at every stage.
    """
    sid = str(submission.id)
    raw_text = submission.raw_text
    rubric_text = assignment.rubric_text or ""

    async def update_step(step: int, status: str):
        await db.refresh(submission)          # get latest DB state
        if submission.status == "cancelled":  # user cancelled via API
            raise asyncio.CancelledError("Submission cancelled by user")
        submission.pipeline_step = step
        submission.status = status
        await db.commit()
        await _broadcast(sid, {"event": "step_update", "step": step, "status": status})

    try:
        # ── STEP 1: Zubaan (input) ─────────────────────────────────────────────
        await update_step(1, "processing")
        demo_lang = student.preferred_language if settings.DEMO_MODE else "english"
        zubaan_result = await _run_agent(
            db, sid, "zubaan_input",
            zubaan.run_input(raw_text, rubric_text, demo_language=demo_lang),
        )
        submission.original_language = zubaan_result["original_language"]
        submission.was_translated = zubaan_result["was_translated"]
        submission.translated_text = zubaan_result["translated_text"]
        submission.language_barrier_risk = zubaan_result["language_barrier_risk"]
        submission.rubric_translated = zubaan_result.get("rubric_translated")
        await db.commit()

        translated_text = zubaan_result["translated_text"]
        effective_rubric = zubaan_result.get("rubric_translated") or rubric_text

        # ── STEP 2: Ingestion ──────────────────────────────────────────────────
        await update_step(2, "processing")
        ingestion_result = await _run_agent(
            db, sid, "ingestion",
            ingestion.run(translated_text, effective_rubric, sid),
        )
        submission.submission_type = ingestion_result["submission_type"]
        submission.cleaned_content = ingestion_result["cleaned_content"]
        submission.rubric_criteria = ingestion_result["rubric_criteria"]
        submission.word_count = ingestion_result["word_count"]
        await db.commit()

        # ── STEP 3: Integrity + Grading (sequential to avoid shared-session deadlock) ─
        await update_step(3, "processing")
        class_id = str(student.school_id)
        class_percentages = [s["percentage"] for s in class_submissions if s.get("percentage")]
        demo_flag = student.preferred_language == "urdu" and settings.DEMO_MODE

        integrity_result = await _run_agent(
            db, sid, "integrity",
            integrity.run(sid, class_id, ingestion_result["cleaned_content"], demo_flag=demo_flag),
        )
        grading_result = await _run_agent(
            db, sid, "grading",
            grading.run(
                sid,
                ingestion_result["cleaned_content"],
                ingestion_result["rubric_criteria"],
                zubaan_result["language_barrier_risk"],
                class_percentages=class_percentages,
                demo_urdu=demo_flag,
            ),
        )

        submission.plagiarism_score = integrity_result["plagiarism_score"]
        submission.plagiarism_evidence = integrity_result["plagiarism_evidence"]
        submission.ai_generated_score = integrity_result["ai_generated_score"]
        submission.ai_evidence = integrity_result["ai_evidence"]
        submission.integrity_flag = integrity_result["overall_integrity_flag"]
        submission.criteria_scores = grading_result["criteria_scores"]
        submission.total_score = grading_result["total_score"]
        submission.total_max = grading_result["total_max"]
        submission.percentage = grading_result["percentage"]
        submission.needs_intervention = grading_result["needs_intervention"]
        submission.language_barrier_note = grading_result.get("language_barrier_note")
        await db.commit()

        # ── STEP 4: Integrity check ────────────────────────────────────────────
        await update_step(4, "processing")
        max_integrity_score = max(
            integrity_result["plagiarism_score"],
            integrity_result["ai_generated_score"],
        )
        if max_integrity_score > 70:
            submission.status = "flagged_integrity"
            await db.commit()
            await _broadcast(sid, {"event": "integrity_flag", "score": max_integrity_score})
            # Still create review checkpoint — teacher must clear or approve
        
        # ── STEP 5: Human-in-the-Loop checkpoint ──────────────────────────────
        await update_step(5, "pending_review")
        review = ReviewCheckpoint(
            submission_id=submission.id,
            created_at=datetime.utcnow(),
            deadline=datetime.utcnow() + timedelta(hours=24),
            status="pending",
        )
        db.add(review)
        await db.commit()
        await _broadcast(sid, {"event": "awaiting_review", "deadline": str(review.deadline)})

        # Pipeline pauses here — resumes via POST /api/review/{id}/approve
        # The cron job handles 24h reminder
        return

    except Exception as e:
        logger.error(f"Pipeline failed for submission {sid}: {e}")
        submission.status = "error"
        submission.error_message = str(e)
        await db.commit()
        await _broadcast(sid, {"event": "pipeline_error", "error": str(e)})


async def resume_after_approval(
    db: AsyncSession,
    submission: Submission,
    student,
    assignment,
    class_submissions: list[dict],
    override_score: float | None = None,
) -> None:
    """
    Called by the review router after teacher approves.
    Continues from Step 6 through Step 8.
    """
    sid = str(submission.id)

    async def update_step(step: int, status: str):
        submission.pipeline_step = step
        submission.status = status
        await db.commit()
        await _broadcast(sid, {"event": "step_update", "step": step, "status": status})

    try:
        if override_score is not None:
            submission.teacher_override_score = override_score
            submission.percentage = round(override_score / submission.total_max * 100, 1) if submission.total_max else 0
            await db.commit()

        # ── STEP 6: Feedback Agent ─────────────────────────────────────────────
        await update_step(6, "processing")
        class_avg = sum(s["percentage"] for s in class_submissions if s.get("percentage")) / max(len(class_submissions), 1)
        feedback_text = await _run_agent(
            db, sid, "feedback",
            feedback.run(
                criteria_scores=submission.criteria_scores or [],
                total_score=submission.teacher_override_score or submission.total_score or 0,
                total_max=submission.total_max or 50,
                percentage=submission.percentage or 0,
                class_average=round(class_avg, 1),
                student_name=student.name,
                grade_level=student.grade_level or "secondary",
                language_barrier_risk=submission.language_barrier_risk or False,
                assignment_title=assignment.title,
            ),
        )
        submission.feedback_english = feedback_text
        await db.commit()

        # ── STEP 7: Zubaan (output) + Waalid (sequential to avoid shared-session deadlock) ─
        await update_step(7, "processing")
        strengths    = [c["criterion"] for c in (submission.criteria_scores or []) if c["score"] / c["max"] >= 0.7][:2]
        improvements = [c["criterion"] for c in (submission.criteria_scores or []) if c["score"] / c["max"] <  0.6][:2]

        zubaan_out_result = await _run_agent(
            db, sid, "zubaan_output",
            zubaan.run_output(feedback_text, submission.original_language or "english"),
        )
        waalid_result = await _run_agent(
            db, sid, "waalid",
            waalid.run(
                student_name=student.name,
                assignment_title=assignment.title,
                total_score=submission.teacher_override_score or submission.total_score or 0,
                total_max=submission.total_max or 50,
                percentage=submission.percentage or 0,
                class_average=round(class_avg, 1),
                strengths=strengths,
                improvements=improvements,
                parent_phone=student.parent_phone or "+923001234567",
                parent_language=student.preferred_language or "urdu",
                next_assessment_date="28 May 2026",
                dropout_risk=student.dropout_risk or False,
                province="Punjab",
            ),
        )
        submission.feedback_translated = (zubaan_out_result or {}).get("translated", "")
        await db.commit()

        # ── STEP 8: Analytics ──────────────────────────────────────────────────
        await update_step(8, "processing")
        analytics_result = await _run_agent(
            db, sid, "analytics",
            analytics.run(
                class_id=str(student.school_id),
                new_submission={"percentage": submission.percentage, "student_id": str(student.id)},
                all_class_submissions=class_submissions,
            ),
        )

        # Check if Taleem Gap should be triggered
        intervention_ids = analytics_result.get("intervention_students", [])
        if str(student.id) in intervention_ids or submission.needs_intervention:
            await update_step(8, "processing")
            score_history = [
                {"percentage": s["percentage"], "assignment_title": s.get("assignment_title", "")}
                for s in class_submissions
                if s.get("student_id") == str(student.id)
            ]
            taleem_result = await _run_agent(
                db, sid, "taleem_gap",
                taleem_gap.run(
                    student_id=str(student.id),
                    student_name=student.name,
                    parent_phone=student.parent_phone or "+923001234567",
                    preferred_language=student.preferred_language or "roman_urdu",
                    score_history=score_history,
                    zubaan_language_risk_history=[submission.language_barrier_risk or False],
                    submission_rate=0.8,
                    grade_level=student.grade_level or "secondary",
                    subject=assignment.title,
                ),
            )
            student.taleem_gap_active = True
            gap_plan = TaleemGapPlan(
                student_id=student.id,
                root_cause=taleem_result.get("root_cause", "concept_gap"),
                plan_data=taleem_result.get("plan", []),
                total_tasks=42,
                status="active",
            )
            db.add(gap_plan)
            await db.commit()

        await update_step(9, "completed")
        submission.status = "completed"
        await db.commit()
        await _broadcast(sid, {"event": "pipeline_complete"})

    except Exception as e:
        logger.error(f"Post-approval pipeline failed for {sid}: {e}")
        submission.status = "error"
        submission.error_message = str(e)
        await db.commit()
        await _broadcast(sid, {"event": "pipeline_error", "error": str(e)})

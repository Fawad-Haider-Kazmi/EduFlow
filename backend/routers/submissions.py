"""
EduFlow — Submissions Router
POST /api/submissions  — accept & queue new submission
GET  /api/submissions  — list all submissions
GET  /api/submissions/{id} — full detail
"""

import asyncio
import uuid
from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from database import Assignment, Student, Submission, Teacher, AgentLog, get_db, AsyncSessionLocal
import orchestrator

router = APIRouter()


class SubmissionCreate(BaseModel):
    student_id: str
    assignment_id: str
    raw_text: str


@router.post("")
async def create_submission(
    body: SubmissionCreate,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
):
    student = await db.get(Student, uuid.UUID(body.student_id))
    assignment = await db.get(Assignment, uuid.UUID(body.assignment_id))
    if not student or not assignment:
        raise HTTPException(404, "Student or Assignment not found")
    teacher = await db.get(Teacher, student.teacher_id)

    submission = Submission(
        student_id=student.id,
        assignment_id=assignment.id,
        raw_text=body.raw_text,
        status="queued",
        pipeline_step=0,
    )
    db.add(submission)
    await db.commit()
    await db.refresh(submission)

    class_subs_result = await db.execute(
        select(Submission).where(
            Submission.assignment_id == assignment.id,
            Submission.status == "completed",
        )
    )
    class_submissions = [
        {
            "student_id": str(s.student_id),
            "percentage": s.percentage,
            "criteria_scores": s.criteria_scores or [],
            "assignment_title": assignment.title,
            "submitted_at": str(s.submitted_at),
        }
        for s in class_subs_result.scalars().all()
    ]

    background_tasks.add_task(_run_new_pipeline, str(submission.id))
    return {"submission_id": str(submission.id), "status": "queued", "ws_url": f"/ws/pipeline/{submission.id}"}


async def _run_new_pipeline(submission_id: str) -> None:
    """
    Background task entry-point. Opens a FRESH database session so the pipeline
    does not inherit the closed request-scoped session from the HTTP handler.
    """
    from sqlalchemy import select as sa_select
    async with AsyncSessionLocal() as db:
        result = await db.execute(
            sa_select(Submission, Student, Assignment, Teacher)
            .join(Student, Submission.student_id == Student.id)
            .join(Assignment, Submission.assignment_id == Assignment.id)
            .join(Teacher, Student.teacher_id == Teacher.id)
            .where(Submission.id == uuid.UUID(submission_id))
        )
        row = result.first()
        if not row:
            return
        submission, student, assignment, teacher = row

        # Build class_submissions from completed subs for the same assignment
        class_result = await db.execute(
            sa_select(Submission).where(
                Submission.assignment_id == assignment.id,
                Submission.status == "completed",
            )
        )
        class_submissions = [
            {
                "student_id": str(s.student_id),
                "percentage": s.percentage,
                "criteria_scores": s.criteria_scores or [],
                "assignment_title": assignment.title,
                "submitted_at": str(s.submitted_at),
            }
            for s in class_result.scalars().all()
        ]
        await orchestrator.run_pipeline(
            db, submission, student, assignment, teacher, class_submissions
        )


@router.get("")
async def list_submissions(db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(Submission, Student, Assignment)
        .join(Student, Submission.student_id == Student.id)
        .join(Assignment, Submission.assignment_id == Assignment.id)
        .order_by(Submission.submitted_at.desc())
    )
    return [
        {
            "id": str(s.id), "student_name": st.name, "assignment_title": a.title,
            "status": s.status, "pipeline_step": s.pipeline_step, "percentage": s.percentage,
            "integrity_flag": s.integrity_flag, "submitted_at": str(s.submitted_at),
            "original_language": s.original_language,
        }
        for s, st, a in result.all()
    ]


@router.get("/{submission_id}")
async def get_submission(submission_id: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(Submission, Student, Assignment)
        .join(Student, Submission.student_id == Student.id)
        .join(Assignment, Submission.assignment_id == Assignment.id)
        .where(Submission.id == uuid.UUID(submission_id))
    )
    row = result.first()
    if not row:
        raise HTTPException(404, "Submission not found")
    s, st, a = row

    logs_result = await db.execute(
        select(AgentLog).where(AgentLog.submission_id == s.id).order_by(AgentLog.called_at)
    )
    logs = [
        {"agent": l.agent_name, "status": l.status, "called_at": str(l.called_at),
         "duration_ms": l.duration_ms, "output": l.output_data}
        for l in logs_result.scalars().all()
    ]

    return {
        "id": str(s.id),
        "student": {"id": str(st.id), "name": st.name, "language": st.preferred_language, "grade": st.grade_level},
        "assignment": {"id": str(a.id), "title": a.title},
        "status": s.status, "pipeline_step": s.pipeline_step, "submitted_at": str(s.submitted_at),
        "raw_text": s.raw_text, "original_language": s.original_language,
        "was_translated": s.was_translated, "translated_text": s.translated_text,
        "language_barrier_risk": s.language_barrier_risk, "submission_type": s.submission_type,
        "word_count": s.word_count,
        "integrity": {
            "plagiarism_score": s.plagiarism_score, "plagiarism_evidence": s.plagiarism_evidence,
            "ai_generated_score": s.ai_generated_score, "ai_evidence": s.ai_evidence, "flag": s.integrity_flag,
        },
        "grading": {
            "criteria_scores": s.criteria_scores, "total_score": s.total_score,
            "total_max": s.total_max, "percentage": s.percentage,
            "needs_intervention": s.needs_intervention, "language_barrier_note": s.language_barrier_note,
        },
        "feedback": {"english": s.feedback_english, "translated": s.feedback_translated},
        "agent_logs": logs,
    }


@router.post("/{submission_id}/cancel")
async def cancel_submission(submission_id: str, db: AsyncSession = Depends(get_db)):
    """
    Marks a submission as cancelled so the background pipeline halts at its
    next update_step checkpoint. Allows the user to immediately submit a new task.
    """
    sub = await db.get(Submission, uuid.UUID(submission_id))
    if not sub:
        raise HTTPException(404, "Submission not found")
    if sub.status in ("completed", "cancelled"):
        raise HTTPException(400, f"Cannot cancel a submission in state: {sub.status}")
    sub.status = "cancelled"
    sub.error_message = "Cancelled by user"
    sub.pipeline_step = 0
    await db.commit()
    return {"status": "cancelled", "submission_id": submission_id}


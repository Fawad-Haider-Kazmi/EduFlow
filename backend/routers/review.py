"""
EduFlow — Review Router (HITL Checkpoint)
POST /api/review/{id}/approve  — teacher approves grade
POST /api/review/{id}/override — teacher overrides with new score
POST /api/review/{id}/flag     — teacher flags for further investigation
GET  /api/review/pending       — all pending reviews
"""

import uuid
from datetime import datetime
from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from database import Assignment, ReviewCheckpoint, Student, Submission, get_db, AsyncSessionLocal
import orchestrator

router = APIRouter()


class OverrideBody(BaseModel):
    override_score: float
    comment: str | None = None


class FlagBody(BaseModel):
    reason: str


@router.get("/pending")
async def list_pending(db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(ReviewCheckpoint, Submission, Student, Assignment)
        .join(Submission, ReviewCheckpoint.submission_id == Submission.id)
        .join(Student, Submission.student_id == Student.id)
        .join(Assignment, Submission.assignment_id == Assignment.id)
        .where(ReviewCheckpoint.status == "pending")
        .order_by(ReviewCheckpoint.deadline)
    )
    return [
        {
            "review_id": str(r.id),
            "submission_id": str(s.id),
            "student_name": st.name,
            "assignment_title": a.title,
            "percentage": s.percentage,
            "integrity_flag": s.integrity_flag,
            "deadline": str(r.deadline),
            "created_at": str(r.created_at),
        }
        for r, s, st, a in result.all()
    ]


@router.post("/{submission_id}/approve")
async def approve(
    submission_id: str,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
):
    submission, review, student, assignment = await _load(submission_id, db)
    review.status = "approved"
    review.reviewed_at = datetime.utcnow()
    submission.teacher_approved = True
    submission.reviewed_at = datetime.utcnow()
    await db.commit()

    # Pass only primitive IDs — background task opens its own fresh session
    background_tasks.add_task(_run_resume_pipeline, submission_id, None)
    return {"status": "approved", "message": "Pipeline resuming from Step 6."}


@router.post("/{submission_id}/override")
async def override(
    submission_id: str,
    body: OverrideBody,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
):
    submission, review, student, assignment = await _load(submission_id, db)
    review.status = "overridden"
    review.override_score = body.override_score
    review.reviewed_at = datetime.utcnow()
    submission.teacher_approved = True
    submission.reviewed_at = datetime.utcnow()
    await db.commit()

    # Pass only primitive IDs — background task opens its own fresh session
    background_tasks.add_task(_run_resume_pipeline, submission_id, body.override_score)
    return {"status": "overridden", "new_score": body.override_score}


@router.post("/{submission_id}/flag")
async def flag(
    submission_id: str,
    body: FlagBody,
    db: AsyncSession = Depends(get_db),
):
    submission, review, *_ = await _load(submission_id, db)
    review.status = "flagged"
    review.reviewed_at = datetime.utcnow()
    submission.status = "flagged_teacher"
    submission.error_message = body.reason
    await db.commit()
    return {"status": "flagged", "reason": body.reason}


async def _run_resume_pipeline(submission_id: str, override_score: float | None) -> None:
    """
    Background task entry-point. Opens a FRESH database session so the pipeline
    does not inherit the closed request-scoped session from the HTTP handler.
    """
    async with AsyncSessionLocal() as db:
        result = await db.execute(
            select(Submission, Student, Assignment)
            .join(Student, Submission.student_id == Student.id)
            .join(Assignment, Submission.assignment_id == Assignment.id)
            .where(Submission.id == uuid.UUID(submission_id))
        )
        row = result.first()
        if not row:
            return
        submission, student, assignment = row
        class_submissions = await _class_submissions(db, submission.assignment_id)
        await orchestrator.resume_after_approval(
            db, submission, student, assignment, class_submissions, override_score
        )


async def _load(submission_id: str, db: AsyncSession):
    result = await db.execute(
        select(Submission, ReviewCheckpoint, Student, Assignment)
        .join(ReviewCheckpoint, ReviewCheckpoint.submission_id == Submission.id)
        .join(Student, Submission.student_id == Student.id)
        .join(Assignment, Submission.assignment_id == Assignment.id)
        .where(Submission.id == uuid.UUID(submission_id))
    )
    row = result.first()
    if not row:
        raise HTTPException(404, "Submission not found or has no review checkpoint")
    s, r, st, a = row

    # If the submission is still pending_review but the checkpoint was already
    # processed (e.g. demo re-use / seed inconsistency), auto-reset so teacher
    # can always take action on a visually pending submission.
    if r.status != "pending" and s.status == "pending_review":
        r.status = "pending"
        r.reviewed_at = None
        await db.commit()
        await db.refresh(r)

    if r.status != "pending":
        raise HTTPException(
            400,
            f"This submission has already been reviewed (status: {r.status}). "
            "Refresh the page to see the current state."
        )
    return s, r, st, a


async def _class_submissions(db, assignment_id):
    result = await db.execute(
        select(Submission).where(
            Submission.assignment_id == assignment_id,
            Submission.status == "completed",
        )
    )
    return [
        {"student_id": str(s.student_id), "percentage": s.percentage,
         "criteria_scores": s.criteria_scores or []}
        for s in result.scalars().all()
    ]

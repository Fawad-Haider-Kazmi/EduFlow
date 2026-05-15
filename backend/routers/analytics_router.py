"""
EduFlow — Analytics Router
GET /api/analytics/class/{class_id}    — class-wide trends
GET /api/analytics/student/{student_id} — per-student history
GET /api/analytics/summary             — demo summary for dashboard cards
"""

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from database import Submission, Student, Assignment, TaleemGapPlan, get_db
import agents.analytics_agent as analytics_agent

router = APIRouter()


@router.get("/summary")
async def get_summary(db: AsyncSession = Depends(get_db)):
    """Dashboard home stats cards."""
    from database import ReviewCheckpoint, GhostSchoolAlert
    from sqlalchemy import func

    pending_count_result = await db.execute(
        select(func.count(ReviewCheckpoint.id)).where(ReviewCheckpoint.status == "pending")
    )
    pending = pending_count_result.scalar() or 0

    intervention_result = await db.execute(
        select(func.count(Student.id)).where(Student.taleem_gap_active == True)
    )
    interventions = intervention_result.scalar() or 0

    ghost_result = await db.execute(
        select(func.count(GhostSchoolAlert.id)).where(GhostSchoolAlert.resolved == False)
    )
    ghost_alerts = ghost_result.scalar() or 0

    completed_result = await db.execute(
        select(Submission).where(Submission.status == "completed")
    )
    completed = completed_result.scalars().all()
    avg = round(sum(s.percentage or 0 for s in completed) / max(len(completed), 1), 1)

    return {
        "pending_reviews": pending,
        "class_average": avg,
        "intervention_students": interventions,
        "ghost_school_alerts": ghost_alerts,
        "total_submissions": len(completed),
    }


@router.get("/class/{class_id}")
async def get_class_analytics(class_id: str, db: AsyncSession = Depends(get_db)):
    return await analytics_agent.run(class_id=class_id, new_submission={}, all_class_submissions=[])


@router.get("/student/{student_id}")
async def get_student_history(student_id: str, db: AsyncSession = Depends(get_db)):
    from sqlalchemy import select
    import uuid
    result = await db.execute(
        select(Submission, Assignment)
        .join(Assignment, Submission.assignment_id == Assignment.id)
        .where(Submission.student_id == uuid.UUID(student_id))
        .order_by(Submission.submitted_at)
    )
    rows = result.all()
    return [
        {
            "assignment": a.title,
            "percentage": s.percentage,
            "submitted_at": str(s.submitted_at),
            "status": s.status,
            "needs_intervention": s.needs_intervention,
        }
        for s, a in rows
    ]

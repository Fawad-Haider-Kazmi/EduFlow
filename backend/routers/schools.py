"""
EduFlow — Schools & Alerts Router
GET /api/schools          — all schools with ghost alert status
GET /api/alerts           — all active alerts (ghost, intervention, errors)
"""

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from database import GhostSchoolAlert, School, Student, Submission, get_db

router = APIRouter()


@router.get("")
async def list_schools(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(School))
    schools = result.scalars().all()
    out = []
    for school in schools:
        alerts_result = await db.execute(
            select(GhostSchoolAlert).where(
                GhostSchoolAlert.school_id == school.id,
                GhostSchoolAlert.resolved == False,
            )
        )
        alerts = alerts_result.scalars().all()
        out.append({
            "id": str(school.id),
            "name": school.name,
            "district": school.district,
            "province": school.province,
            "last_submission_date": str(school.last_submission_date) if school.last_submission_date else None,
            "is_active": school.is_active,
            "open_alerts": len(alerts),
            "alert_types": list({a.flag_type for a in alerts}),
        })
    return out


@router.get("/alerts")
async def list_alerts(db: AsyncSession = Depends(get_db)):
    # Ghost school alerts
    ghost_result = await db.execute(
        select(GhostSchoolAlert, School)
        .join(School, GhostSchoolAlert.school_id == School.id)
        .where(GhostSchoolAlert.resolved == False)
        .order_by(GhostSchoolAlert.created_at.desc())
    )
    ghost_alerts = [
        {
            "type": "ghost_school",
            "school_name": school.name,
            "district": school.district,
            "flag_type": a.flag_type,
            "weeks_silent": a.weeks_silent,
            "escalation_step": a.escalation_step,
            "admin_notified": a.admin_notified,
            "deo_escalated": a.deo_escalated,
            "created_at": str(a.created_at),
        }
        for a, school in ghost_result.all()
    ]

    # Intervention alerts
    intervention_result = await db.execute(
        select(Student).where(Student.taleem_gap_active == True)
    )
    intervention_alerts = [
        {
            "type": "intervention",
            "student_name": s.name,
            "student_id": str(s.id),
            "dropout_risk": s.dropout_risk,
        }
        for s in intervention_result.scalars().all()
    ]

    # Error submissions
    error_result = await db.execute(
        select(Submission).where(Submission.status == "error")
    )
    error_alerts = [
        {
            "type": "pipeline_error",
            "submission_id": str(s.id),
            "error": s.error_message,
            "submitted_at": str(s.submitted_at),
        }
        for s in error_result.scalars().all()
    ]

    return {
        "ghost_school": ghost_alerts,
        "intervention": intervention_alerts,
        "errors": error_alerts,
        "total": len(ghost_alerts) + len(intervention_alerts) + len(error_alerts),
    }

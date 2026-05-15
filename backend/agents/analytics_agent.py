"""
AGENT 6 — Analytics Agent
Class-wide trend analysis and intervention flagging. Runs after every approved batch.
"""

import logging
import statistics
from typing import Any

from config import settings

logger = logging.getLogger(__name__)

DEMO_OUTPUT = {
    "class_average": 64,
    "weakest_criteria": ["Use of Evidence", "Critical Thinking"],
    "strongest_criteria": ["Structure & Organisation"],
    "intervention_students": ["student-bilal-id", "student-fatima-id"],
    "trend_summary": "Class average improved 4% from last assignment. 2 students flagged for intervention.",
    "teacher_summary": "Most students struggled with Use of Evidence (class avg: 44%) and Critical Thinking (avg: 51%). 2 students have scored below 50% on 2 consecutive assignments and have been referred to the Taleem Gap program. Top performer: Zain Ul Abideen (88%).",
    "criterion_breakdown": [
        {"criterion": "Argument Clarity", "class_avg": 74, "below_60_count": 1},
        {"criterion": "Use of Evidence", "class_avg": 44, "below_60_count": 4},
        {"criterion": "Structure & Organisation", "class_avg": 81, "below_60_count": 0},
        {"criterion": "Language Quality", "class_avg": 68, "below_60_count": 2},
        {"criterion": "Critical Thinking", "class_avg": 51, "below_60_count": 3},
    ],
    "student_trends": [
        {"student_id": "student-ahmed-id", "name": "Ahmed Ali", "trend": "improving", "last_3": [58, 65, 72]},
        {"student_id": "student-sara-id", "name": "Sara Malik", "trend": "stable", "last_3": [61, 63, 62]},
        {"student_id": "student-bilal-id", "name": "Bilal Ahmed", "trend": "declining", "last_3": [55, 47, 44]},
        {"student_id": "student-fatima-id", "name": "Fatima Noor", "trend": "declining", "last_3": [48, 42, 38]},
        {"student_id": "student-zain-id", "name": "Zain Ul Abideen", "trend": "improving", "last_3": [75, 82, 88]},
    ],
}


async def run(
    class_id: str,
    new_submission: dict,
    all_class_submissions: list[dict],
) -> dict[str, Any]:
    """
    Analyses class-wide performance. Returns structured report for teacher dashboard.
    Also returns list of student_ids that need Taleem Gap intervention.
    """
    if settings.DEMO_MODE:
        return DEMO_OUTPUT

    percentages = [s["percentage"] for s in all_class_submissions if s.get("percentage") is not None]
    if not percentages:
        return {"class_average": 0, "intervention_students": [], "teacher_summary": "No data yet."}

    class_avg = round(statistics.mean(percentages), 1)

    # Criterion-level breakdown
    criterion_data: dict[str, list[float]] = {}
    for sub in all_class_submissions:
        for c in sub.get("criteria_scores", []):
            name = c["criterion"]
            pct = (c["score"] / c["max"] * 100) if c.get("max") else 0
            criterion_data.setdefault(name, []).append(pct)

    criterion_breakdown = []
    for name, scores in criterion_data.items():
        avg = round(statistics.mean(scores), 1)
        below_60 = sum(1 for s in scores if s < 60)
        criterion_breakdown.append({"criterion": name, "class_avg": avg, "below_60_count": below_60})

    weakest = sorted(criterion_breakdown, key=lambda x: x["class_avg"])[:2]
    strongest = sorted(criterion_breakdown, key=lambda x: x["class_avg"], reverse=True)[:1]

    # Intervention: below 50% on 2+ consecutive assignments
    intervention_students = []
    student_history: dict[str, list[float]] = {}
    for sub in sorted(all_class_submissions, key=lambda x: x.get("submitted_at", "")):
        sid = sub.get("student_id")
        pct = sub.get("percentage")
        if sid and pct is not None:
            student_history.setdefault(sid, []).append(pct)

    for sid, history in student_history.items():
        if len(history) >= 2 and all(h < 50 for h in history[-2:]):
            intervention_students.append(sid)

    return {
        "class_average": class_avg,
        "weakest_criteria": [c["criterion"] for c in weakest],
        "strongest_criteria": [c["criterion"] for c in strongest],
        "intervention_students": intervention_students,
        "criterion_breakdown": criterion_breakdown,
        "trend_summary": f"Class average: {class_avg}%. {len(intervention_students)} student(s) flagged for intervention.",
        "teacher_summary": (
            f"Class average is {class_avg}%. "
            f"Most students struggled with {', '.join(c['criterion'] for c in weakest)}. "
            f"{len(intervention_students)} student(s) have been referred to the Taleem Gap program."
        ),
    }

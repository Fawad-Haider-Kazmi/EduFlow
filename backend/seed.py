"""
EduFlow Pakistan — Demo Seed Script
Run once to populate the database with demo data for live demos.

Usage:
    cd backend
    python seed.py

Seeds:
    - 2 schools (1 active, 1 ghost)
    - 1 teacher (auto-login on demo start)
    - 5 students (2 Taleem Gap, 1 dropout risk)
    - 3 assignments
    - Pre-graded submissions (3 per student = 15 total)
    - 1 mid-processing submission (for live pipeline demo)
    - 1 ghost school alert (Quetta, 3 weeks silent)
    - 2 Taleem Gap plans (Bilal + Fatima)
"""

import asyncio
import uuid
from datetime import datetime, timedelta

# ── Fixed UUIDs for demo repeatability ────────────────────────────────────────
SCHOOL_LAHORE_ID  = uuid.UUID("aaaaaaaa-0001-0001-0001-000000000001")
SCHOOL_QUETTA_ID  = uuid.UUID("aaaaaaaa-0002-0001-0001-000000000002")
TEACHER_ID        = uuid.UUID("bbbbbbbb-0001-0001-0001-000000000001")
STUDENT_AHMED_ID  = uuid.UUID("cccccccc-0001-0001-0001-000000000001")
STUDENT_SARA_ID   = uuid.UUID("cccccccc-0002-0001-0001-000000000002")
STUDENT_BILAL_ID  = uuid.UUID("cccccccc-0003-0001-0001-000000000003")
STUDENT_FATIMA_ID = uuid.UUID("cccccccc-0004-0001-0001-000000000004")
STUDENT_ZAIN_ID   = uuid.UUID("cccccccc-0005-0001-0001-000000000005")
ASSIGN_1_ID       = uuid.UUID("dddddddd-0001-0001-0001-000000000001")
ASSIGN_2_ID       = uuid.UUID("dddddddd-0002-0001-0001-000000000002")
ASSIGN_3_ID       = uuid.UUID("dddddddd-0003-0001-0001-000000000003")

NOW = datetime.utcnow()


RUBRIC = """
Criterion 1 — Argument Clarity (10 pts): Thesis is clear and well-supported.
Criterion 2 — Use of Evidence (10 pts): Historical facts and examples cited accurately.
Criterion 3 — Structure & Organisation (10 pts): Clear intro, body, conclusion.
Criterion 4 — Language Quality (10 pts): Grammar and vocabulary appropriate for grade level.
Criterion 5 — Critical Thinking (10 pts): Analysis beyond fact recitation.
"""

RUBRIC_CRITERIA = [
    {"criterion": "Argument Clarity", "max_points": 10, "description": "Thesis is clear and well-supported."},
    {"criterion": "Use of Evidence", "max_points": 10, "description": "Historical facts cited accurately."},
    {"criterion": "Structure & Organisation", "max_points": 10, "description": "Clear intro, body, conclusion."},
    {"criterion": "Language Quality", "max_points": 10, "description": "Grammar and vocabulary appropriate."},
    {"criterion": "Critical Thinking", "max_points": 10, "description": "Analysis beyond fact recitation."},
]

# Per-student, per-assignment grade profiles (to show trends)
GRADE_PROFILES = {
    "ahmed":  [{"scores": [8,6,9,7,6]}, {"scores": [8,7,9,8,7]}, {"scores": [9,8,9,7,7]}],   # improving
    "sara":   [{"scores": [6,5,7,5,5]}, {"scores": [6,6,7,5,6]}, {"scores": [6,6,7,6,5]}],   # stable
    "bilal":  [{"scores": [5,4,6,4,4]}, {"scores": [4,3,5,4,3]}, {"scores": [4,3,5,3,3]}],   # declining → Taleem Gap
    "fatima": [{"scores": [4,3,5,3,4]}, {"scores": [3,2,4,3,3]}, {"scores": [3,2,4,2,3]}],   # declining → Taleem Gap + dropout
    "zain":   [{"scores": [9,8,9,8,8]}, {"scores": [9,9,9,8,9]}, {"scores": [10,9,10,9,9]}], # top performer
}

CRITERIA_LABELS = ["Argument Clarity", "Use of Evidence", "Structure & Organisation", "Language Quality", "Critical Thinking"]

RAW_TEXTS = {
    "ahmed":  "Pakistan gained independence on August 14, 1947, after a long struggle led by Muhammad Ali Jinnah. The partition of British India was a pivotal moment in history. Pakistan's founding was the result of decades of political movement, sacrifice, and determination by the Muslim League and its supporters across the subcontinent.",
    "sara":   "پاکستان 14 اگست 1947 کو آزاد ہوا۔ قائداعظم محمد علی جناح نے مسلم لیگ کی قیادت کی۔ تقسیم ہند کے نتیجے میں دو نئی مملکتیں وجود میں آئیں۔",
    "bilal":  "Pakistan bana 1947 mein. Quaid e Azam ne help ki. Angraizon ne India ko taqseem kiya. Pakistan ka matlab hai La ilaha illallah.",
    "fatima": "پاکستان ایک اسلامی ملک ہے جو 1947 میں بنا۔ یہاں مسلمان رہتے ہیں۔",
    "zain":   "Pakistan's independence in 1947 was not merely a political event but a civilisational milestone. The two-nation theory articulated by Allama Iqbal and operationalised by Jinnah represented a sophisticated argument about identity, governance, and self-determination. The Lahore Resolution of 1940 laid the constitutional groundwork for what would become the world's first nation created in the name of Islam.",
}


def make_criteria_scores(scores: list[int]) -> list[dict]:
    rationales = [
        "Thesis statement is clear but could be strengthened with more supporting detail.",
        "Some evidence provided but more specific historical references would improve this section.",
        "Essay structure is logical with clear introduction and conclusion.",
        "Language is appropriate for the grade level with minor grammatical issues.",
        "Shows some analytical thinking but mostly descriptive rather than evaluative.",
    ]
    cited = [
        "Pakistan gained independence on August 14, 1947...",
        "The partition of British India created two new nations.",
        "In conclusion, Pakistan's independence remains a defining moment...",
        "led by Muhammad Ali Jinnah and the Muslim League",
        "Pakistan's founding was the result of decades of political movement",
    ]
    return [
        {
            "criterion": CRITERIA_LABELS[i],
            "score": scores[i],
            "max": 10,
            "rationale": rationales[i],
            "cited_text": cited[i],
        }
        for i in range(5)
    ]


async def seed():
    import sys
    import os
    sys.path.insert(0, os.path.dirname(__file__))

    from database import (
        init_db, AsyncSessionLocal,
        School, Teacher, Student, Assignment, Submission,
        ReviewCheckpoint, GhostSchoolAlert, TaleemGapPlan,
    )

    await init_db()
    async with AsyncSessionLocal() as db:

        # ── Schools ───────────────────────────────────────────────────────────
        lahore = School(
            id=SCHOOL_LAHORE_ID, name="Lahore Model Public School",
            district="Lahore", province="Punjab",
            admin_email="admin@lahoremodel.edu.pk",
            registered_at=NOW - timedelta(days=120),
            is_active=True,
            last_submission_date=NOW - timedelta(days=1),
        )
        quetta = School(
            id=SCHOOL_QUETTA_ID, name="Quetta Secondary School",
            district="Quetta", province="Balochistan",
            admin_email="admin@quettasec.edu.pk",
            registered_at=NOW - timedelta(days=200),
            is_active=True,
            last_submission_date=NOW - timedelta(weeks=3, days=2),
        )
        db.add_all([lahore, quetta])

        # ── Teacher ───────────────────────────────────────────────────────────
        teacher = Teacher(
            id=TEACHER_ID, name="Ms. Ayesha Raza",
            email="ayesha.raza@lahoremodel.edu.pk",
            school_id=SCHOOL_LAHORE_ID,
            created_at=NOW - timedelta(days=90),
        )
        db.add(teacher)

        # ── Students ──────────────────────────────────────────────────────────
        students = [
            Student(id=STUDENT_AHMED_ID,  name="Ahmed Ali",       school_id=SCHOOL_LAHORE_ID, teacher_id=TEACHER_ID, grade_level="secondary", age=15, preferred_language="english",    parent_phone="+923001111001", dropout_risk=False, taleem_gap_active=False),
            Student(id=STUDENT_SARA_ID,   name="Sara Malik",      school_id=SCHOOL_LAHORE_ID, teacher_id=TEACHER_ID, grade_level="secondary", age=14, preferred_language="urdu",       parent_phone="+923001111002", dropout_risk=False, taleem_gap_active=False),
            Student(id=STUDENT_BILAL_ID,  name="Bilal Ahmed",     school_id=SCHOOL_LAHORE_ID, teacher_id=TEACHER_ID, grade_level="secondary", age=15, preferred_language="roman_urdu", parent_phone="+923001111003", dropout_risk=False, taleem_gap_active=True),
            Student(id=STUDENT_FATIMA_ID, name="Fatima Noor",     school_id=SCHOOL_LAHORE_ID, teacher_id=TEACHER_ID, grade_level="secondary", age=13, preferred_language="urdu",       parent_phone="+923001111004", dropout_risk=True,  taleem_gap_active=True),
            Student(id=STUDENT_ZAIN_ID,   name="Zain Ul Abideen", school_id=SCHOOL_LAHORE_ID, teacher_id=TEACHER_ID, grade_level="secondary", age=16, preferred_language="english",    parent_phone="+923001111005", dropout_risk=False, taleem_gap_active=False),
        ]
        db.add_all(students)

        # ── Assignments ───────────────────────────────────────────────────────
        assign_dates = [NOW - timedelta(days=60), NOW - timedelta(days=30), NOW - timedelta(days=7)]
        assignments = [
            Assignment(id=ASSIGN_1_ID, title="Pakistan Independence Essay",  teacher_id=TEACHER_ID, rubric_text=RUBRIC, due_date=assign_dates[0], created_at=assign_dates[0] - timedelta(days=7)),
            Assignment(id=ASSIGN_2_ID, title="Constitutional Development Essay", teacher_id=TEACHER_ID, rubric_text=RUBRIC, due_date=assign_dates[1], created_at=assign_dates[1] - timedelta(days=7)),
            Assignment(id=ASSIGN_3_ID, title="Economic Challenges of Pakistan",  teacher_id=TEACHER_ID, rubric_text=RUBRIC, due_date=assign_dates[2], created_at=assign_dates[2] - timedelta(days=7)),
        ]
        db.add_all(assignments)
        await db.flush()

        # ── Pre-graded Submissions ─────────────────────────────────────────────
        student_keys  = ["ahmed", "sara", "bilal", "fatima", "zain"]
        student_ids   = [STUDENT_AHMED_ID, STUDENT_SARA_ID, STUDENT_BILAL_ID, STUDENT_FATIMA_ID, STUDENT_ZAIN_ID]
        assign_ids    = [ASSIGN_1_ID, ASSIGN_2_ID, ASSIGN_3_ID]

        lang_map = {"ahmed": "english", "sara": "urdu", "bilal": "roman_urdu", "fatima": "urdu", "zain": "english"}
        barrier_map = {"ahmed": False, "sara": True, "bilal": True, "fatima": True, "zain": False}
        integrity_scores = {"ahmed": (12, 18), "sara": (10, 22), "bilal": (15, 20), "fatima": (8, 15), "zain": (5, 12)}

        for ai, (assign_id, assign_date) in enumerate(zip(assign_ids, assign_dates)):
            for si, (key, student_id) in enumerate(zip(student_keys, student_ids)):
                scores = GRADE_PROFILES[key][ai]["scores"]
                criteria = make_criteria_scores(scores)
                total = sum(scores)
                pct = round(total / 50 * 100, 1)
                plag, ai_score = integrity_scores[key]
                sub = Submission(
                    student_id=student_id,
                    assignment_id=assign_id,
                    submitted_at=assign_date - timedelta(days=1),
                    raw_text=RAW_TEXTS[key],
                    status="completed",
                    pipeline_step=9,
                    original_language=lang_map[key],
                    was_translated=lang_map[key] != "english",
                    translated_text=RAW_TEXTS["ahmed"],
                    language_barrier_risk=barrier_map[key],
                    submission_type="essay",
                    cleaned_content=RAW_TEXTS["ahmed"],
                    rubric_criteria=RUBRIC_CRITERIA,
                    word_count=len(RAW_TEXTS[key].split()),
                    plagiarism_score=plag,
                    plagiarism_evidence="No significant overlap detected.",
                    ai_generated_score=ai_score,
                    ai_evidence="Stylometric signals within normal range.",
                    integrity_flag=False,
                    criteria_scores=criteria,
                    total_score=float(total),
                    total_max=50.0,
                    percentage=pct,
                    needs_intervention=pct < 50,
                    language_barrier_note=(
                        "Note: Student submitted in native language. Concept understanding assessed independently."
                        if barrier_map[key] else None
                    ),
                    teacher_approved=True,
                    reviewed_at=assign_date,
                    feedback_english=f"Good effort, {key.title()}! Your essay shows understanding of the key events. Continue working on evidence-based arguments.",
                    feedback_translated=f"[TRANSLATED] Good effort, {key.title()}!",
                )
                db.add(sub)

        # ── Mid-processing submission (for live demo) ─────────────────────────
        live_sub = Submission(
            id=uuid.UUID("eeeeeeee-0001-0001-0001-000000000001"),
            student_id=STUDENT_AHMED_ID,
            assignment_id=ASSIGN_3_ID,
            submitted_at=NOW - timedelta(minutes=5),
            raw_text=RAW_TEXTS["ahmed"],
            status="pending_review",
            pipeline_step=5,
            original_language="english",
            was_translated=False,
            translated_text=RAW_TEXTS["ahmed"],
            language_barrier_risk=False,
            submission_type="essay",
            cleaned_content=RAW_TEXTS["ahmed"],
            rubric_criteria=RUBRIC_CRITERIA,
            word_count=len(RAW_TEXTS["ahmed"].split()),
            plagiarism_score=12.0,
            plagiarism_evidence="No significant semantic overlap detected.",
            ai_generated_score=18.0,
            ai_evidence="Stylometric signals within normal range (std dev: 4.3). Vocabulary richness: 0.71.",
            integrity_flag=False,
            criteria_scores=make_criteria_scores([8, 6, 9, 7, 6]),
            total_score=36.0,
            total_max=50.0,
            percentage=72.0,
            needs_intervention=False,
        )
        db.add(live_sub)

        review_cp = ReviewCheckpoint(
            submission_id=live_sub.id,
            created_at=NOW - timedelta(minutes=5),
            deadline=NOW + timedelta(hours=23, minutes=55),
            status="pending",
        )
        db.add(review_cp)

        # ── Ghost School Alert ─────────────────────────────────────────────────
        ghost_alert = GhostSchoolAlert(
            school_id=SCHOOL_QUETTA_ID,
            flag_type="ghost_school",
            weeks_silent=3,
            last_submission_date=NOW - timedelta(weeks=3, days=2),
            escalation_step=1,
            admin_notified=True,
            admin_notified_at=NOW - timedelta(hours=6),
            deo_escalated=False,
            created_at=NOW - timedelta(hours=6),
            resolved=False,
        )
        db.add(ghost_alert)

        # ── Taleem Gap Plans ──────────────────────────────────────────────────
        bilal_plan = TaleemGapPlan(
            student_id=STUDENT_BILAL_ID,
            root_cause="concept_gap",
            plan_data=[
                {"day": i+1, "tasks": [
                    f"Day {i+1} Task 1: Practice writing one argument with evidence.",
                    f"Day {i+1} Task 2: Find one fact from your textbook to support an idea.",
                    f"Day {i+1} Task 3: Rewrite one weak sentence to make it stronger.",
                ]} for i in range(14)
            ],
            started_at=NOW - timedelta(days=3),
            current_day=4,
            completed_tasks=9,
            total_tasks=42,
            status="active",
        )
        fatima_plan = TaleemGapPlan(
            student_id=STUDENT_FATIMA_ID,
            root_cause="language_barrier",
            plan_data=[
                {"day": i+1, "tasks": [
                    f"Din {i+1} Kaam 1: Ek paragraph mein 3 sentences likho.",
                    f"Din {i+1} Kaam 2: Kitab se ek topic parho aur apne alfaaz mein likho.",
                    f"Din {i+1} Kaam 3: Apni teacher ko ek sawal poochho jo samajh na aaya ho.",
                ]} for i in range(14)
            ],
            started_at=NOW - timedelta(days=5),
            current_day=6,
            completed_tasks=12,
            total_tasks=42,
            status="active",
        )
        db.add_all([bilal_plan, fatima_plan])

        await db.commit()
        print("[OK] Demo data seeded successfully!")
        print(f"   Teacher email: ayesha.raza@lahoremodel.edu.pk")
        print(f"   Demo login:    GET /auth/demo")
        print(f"   Live sub:      {live_sub.id} (status: pending_review)")
        print(f"   Ghost school:  Quetta Secondary School (3 weeks silent)")


if __name__ == "__main__":
    asyncio.run(seed())

"""
AGENT 8 — Taleem Gap Agent (Active Intervention)
Triggered when a student scores below 50% on 2+ consecutive assignments.
Generates a 14-day SNC-aligned recovery plan delivered via WhatsApp.
"""

import logging
from datetime import datetime, timedelta
from typing import Any

from config import settings
from services.llm_service import llm_service
from services.twilio_service import send_whatsapp

logger = logging.getLogger(__name__)

DEMO_PLAN = {
    "root_cause": "concept_gap",
    "diagnosis": "Bilal understands the language but consistently struggles with evidence-based argumentation and critical analysis — a concept gap in essay writing skills.",
    "plan": [
        {"day": 1, "tasks": ["Write 3 sentences using the word 'therefore' to connect an argument to a fact.", "Find one news headline and write one sentence explaining WHY it happened.", "Read 1 paragraph from your textbook and underline all the facts."]},
        {"day": 2, "tasks": ["Write a 5-sentence paragraph about your favourite sport using at least 2 facts.", "Find 2 pieces of evidence from Chapter 4 that support the idea of Pakistan's independence.", "Write: 'My argument is ___ because ___.' Fill in the blank 5 times."]},
        {"day": 3, "tasks": ["Practice: Write a claim + evidence + explanation (CEE) for one topic.", "Rewrite your last essay's weakest paragraph with one added fact.", "List 3 differences between a fact and an opinion."]},
    ],
    "total_tasks": 42,
    "delivery_language": "roman_urdu",
    "day1_message": "Day 1/14 — Bilal: Task 1: 'Therefore' ka istemal kar ke 3 sentences likho. Task 2: Ek news headline lo aur likho KYU hua. Task 3: Textbook se ek paragraph mein sab facts underline karo. Reply DONE jab khatam ho jao!",
}


async def run(
    student_id: str,
    student_name: str,
    parent_phone: str,
    preferred_language: str,
    score_history: list[dict],
    zubaan_language_risk_history: list[bool],
    submission_rate: float,
    grade_level: str,
    subject: str,
) -> dict[str, Any]:
    if settings.DEMO_MODE:
        return DEMO_PLAN

    # ── Step 1: Diagnose root cause ────────────────────────────────────────────
    language_risk_ratio = sum(zubaan_language_risk_history) / max(len(zubaan_language_risk_history), 1)
    if submission_rate < 0.5:
        root_cause = "absenteeism"
    elif language_risk_ratio > 0.6:
        root_cause = "language_barrier"
    elif language_risk_ratio > 0.3:
        root_cause = "mixed"
    else:
        root_cause = "concept_gap"

    score_summary = "\n".join(
        f"Assignment {i+1}: {s['percentage']}% ({s['assignment_title']})"
        for i, s in enumerate(score_history[-4:])
    )

    # ── Step 2: Generate 14-day plan ───────────────────────────────────────────
    lang_note = {
        "roman_urdu": "Write all tasks in Roman Urdu (Urdu in English letters).",
        "urdu": "Write all tasks in Urdu script.",
        "english": "Write all tasks in English.",
    }.get(preferred_language, "Write in Roman Urdu.")

    prompt = f"""
You are creating a 14-day recovery plan for a {grade_level} student named {student_name}.
Subject: {subject}. Root cause: {root_cause}.
{lang_note}

Score history:
{score_summary}

Generate exactly 14 days. Each day has exactly 3 tasks.
Each task takes 15 minutes maximum. Tasks must be PRACTICAL not theoretical.
Structure: Days 1-5 = foundational, Days 6-10 = practice, Days 11-14 = application.
Difficulty increases gradually.

Return JSON:
{{
  "diagnosis": "...",
  "plan": [
    {{"day": 1, "tasks": ["task1", "task2", "task3"]}},
    ...
  ]
}}
"""
    result = await llm_service.generate_json(prompt)

    # ── Step 3: Send Day 1 immediately ────────────────────────────────────────
    day1 = result.get("plan", [{}])[0]
    tasks = day1.get("tasks", [])
    day1_msg = (
        f"Day 1/14 — {student_name}: "
        + " ".join(f"Task {i+1}: {t}" for i, t in enumerate(tasks))
        + " Reply DONE jab khatam ho jao!"
    )
    await send_whatsapp(parent_phone, day1_msg)

    return {
        "root_cause": root_cause,
        "diagnosis": result.get("diagnosis", ""),
        "plan": result.get("plan", []),
        "total_tasks": 42,
        "delivery_language": preferred_language,
        "day1_message": day1_msg,
    }

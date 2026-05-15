"""
AGENT 5 — Feedback Agent
Transforms approved grading output into a warm, age-appropriate student report.
Only called AFTER teacher approves the grade (Step 6).
"""

import logging
from typing import Any

from config import settings
from services.llm_service import llm_service

logger = logging.getLogger(__name__)

DEMO_OUTPUT = """Well done, Ahmed! Your essay on Pakistan's independence shows real effort and a solid grasp of the key events.

What you did well:
Your opening paragraph sets up a strong argument — your thesis about Jinnah's leadership is clear and confident. The essay is well-organised with a logical flow from causes to consequences to conclusion. Your conclusion ties the essay together nicely.

Where to improve:
Try to include specific evidence — dates, statistics, or quotes. Instead of "many people suffered," try "over 14 million people were displaced during partition." Also, paragraph 3 jumps topics without a transition — try adding a linking sentence.

Your score: 36/50 (72%) — above the class average of 64%

Keep it up, Ahmed. With a little more evidence in your arguments, you will be scoring even higher next time!""".strip()


async def run(
    criteria_scores: list[dict],
    total_score: float,
    total_max: float,
    percentage: float,
    class_average: float,
    student_name: str,
    grade_level: str,
    language_barrier_risk: bool,
    assignment_title: str,
) -> str:
    if settings.DEMO_MODE:
        return DEMO_OUTPUT

    tone_map = {
        "primary": "Very simple words, short sentences. Friendly. Emoji welcome.",
        "secondary": "Conversational but clear. Specific and actionable.",
        "higher": "Professional tone. Direct and constructive.",
    }
    tone = tone_map.get(grade_level, tone_map["secondary"])
    rubric_summary = "\n".join(
        f"- {c['criterion']}: {c['score']}/{c['max']} — {c['rationale']}"
        for c in criteria_scores
    )
    barrier_note = (
        "Student wrote in native language — add one line acknowledging their effort.\n"
        if language_barrier_risk else ""
    )
    prompt = f"""
Write a student feedback report for {student_name}, assignment: "{assignment_title}".
Tone: {tone}
{barrier_note}
GRADING:
{rubric_summary}
SCORE: {total_score}/{total_max} ({percentage}%) — class average: {class_average}%

Structure: (1) Opening with genuine strength, (2) 2-3 strengths with examples,
(3) 2-3 improvement areas with concrete suggestions, (4) Score line, (5) Motivating close.
Max 300 words. Second person. No JSON. No markdown headers.
"""
    return await llm_service.generate(prompt)

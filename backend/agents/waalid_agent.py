"""
AGENT 7 — Waalid Agent (Parent Engagement)
Sends Telegram messages to parents. Runs in parallel with Zubaan output (Step 7).
Never responds autonomously to parent replies — forwards to teacher dashboard.
"""

import logging
from typing import Any

from config import settings
from services.llm_service import llm_service
from services.telegram_service import notify_parent_result, notify_dropout_risk as _notify_dropout

logger = logging.getLogger(__name__)

GOVT_SCHEMES = {
    "Punjab": {"name": "Ehsaas Wazaifa", "helpline": "0800-26477"},
    "Sindh": {"name": "Sindh Education Foundation Stipend", "helpline": "021-99251600"},
    "KPK": {"name": "CM Educational Endowment Fund", "helpline": "0800-02345"},
    "Balochistan": {"name": "BISP Education Stipend", "helpline": "0800-26477"},
}

DEMO_PARENT_MESSAGE = (
    "Assalam o Alaikum! Ahmed Ali ka Assignment 3 (Pakistan Independence Essay) ka result aa gaya.\n"
    "Score: 36/50 (72%) — class se behtar. Strong point: argument ki wazahat. Improve: evidence aur proof dena.\n"
    "Ghar mein roz 15 minute essay likhwayein. Agli assessment: 28 May."
)

DEMO_DROPOUT_MESSAGE = (
    "Assalam o Alaikum, Fatima Noor ke walid/walida. Ehtiram ke saath arz hai ke Fatima ki recent "
    "performance concern ka bais hai. Ehsaas Wazaifa (Punjab) ke zariye aapko madad mil sakti hai "
    "taake Fatima school mein reh sake. Helpline: 0800-26477. Madam Ayesha se rabta kar sakte hain."
)


async def run(
    student_name: str,
    assignment_title: str,
    total_score: float,
    total_max: float,
    percentage: float,
    class_average: float,
    strengths: list[str],
    improvements: list[str],
    parent_phone: str,
    parent_language: str,
    next_assessment_date: str,
    dropout_risk: bool = False,
    province: str = "Punjab",
) -> dict[str, Any]:
    if settings.DEMO_MODE:
        return {
            "message_sent": True,
            "parent_message": DEMO_PARENT_MESSAGE,
            "dropout_alert": DEMO_DROPOUT_MESSAGE if dropout_risk else None,
        }

    # ── Main grade message ─────────────────────────────────────────────────────
    lang_instruction = {
        "urdu": "Write in Urdu script.",
        "roman_urdu": "Write in Roman Urdu (Urdu words in English letters).",
        "english": "Write in English.",
    }.get(parent_language, "Write in Urdu script.")

    prompt = f"""
Write a 3-line WhatsApp message for a parent about their child's assignment result.
{lang_instruction}
Format:
Line 1: Greeting + student name + assignment name
Line 2: Score + one strength + one area to work on
Line 3: One thing parent can do at home + next assessment date

Details:
- Student: {student_name}
- Assignment: {assignment_title}
- Score: {total_score}/{total_max} ({percentage}%) — class average: {class_average}%
- Strengths: {', '.join(strengths)}
- Improvements: {', '.join(improvements)}
- Next assessment: {next_assessment_date}

No markdown. Plain text. Under 160 words.
"""
    parent_message = await llm_service.generate(prompt)
    await notify_parent_result(
        chat_id=parent_phone,  # in production, use parent's Telegram chat_id
        student_name=student_name,
        assignment_title=assignment_title,
        score_str=f"{total_score}/{total_max} ({percentage}%)",
        strength=strengths[0] if strengths else "",
        improvement=improvements[0] if improvements else "",
        next_assessment=next_assessment_date,
    )

    # ── Dropout risk alert (separate message) ─────────────────────────────────
    dropout_alert = None
    if dropout_risk:
        scheme = GOVT_SCHEMES.get(province, GOVT_SCHEMES["Punjab"])
        dropout_prompt = f"""
Write a Telegram message to a parent whose child is at dropout risk.
{lang_instruction}
Tone: concerned but supportive, NOT alarming.
Mention: {scheme['name']} government scheme. Helpline: {scheme['helpline']}.
Student: {student_name}. Under 100 words. Plain text only.
"""
        dropout_alert = await llm_service.generate(dropout_prompt)
        await _notify_dropout(
            chat_id=parent_phone,
            student_name=student_name,
            scheme=scheme["name"],
            helpline=scheme["helpline"],
        )

    return {
        "message_sent": True,
        "parent_message": parent_message,
        "dropout_alert": dropout_alert,
    }

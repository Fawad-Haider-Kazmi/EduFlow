"""
AGENT 2 — Ingestion Agent
Cleans translated content and parses the rubric into structured scoring criteria.
"""

import re
import logging
from typing import Any

from config import settings
from services.llm_service import llm_service

logger = logging.getLogger(__name__)

DEMO_OUTPUT = {
    "submission_type": "essay",
    "cleaned_content": "Pakistan gained independence on August 14, 1947, after a long struggle led by Muhammad Ali Jinnah and the Muslim League. The partition of British India created two new nations. Pakistan's independence was the culmination of decades of political movement and sacrifice.",
    "rubric_criteria": [
        {"criterion": "Argument Clarity", "max_points": 10, "description": "Thesis is clear and well-supported throughout the essay"},
        {"criterion": "Use of Evidence", "max_points": 10, "description": "Historical facts and examples are cited accurately"},
        {"criterion": "Structure & Organisation", "max_points": 10, "description": "Essay has a clear introduction, body, and conclusion"},
        {"criterion": "Language Quality", "max_points": 10, "description": "Grammar, spelling, and vocabulary are appropriate for grade level"},
        {"criterion": "Critical Thinking", "max_points": 10, "description": "Student demonstrates analysis beyond recitation of facts"},
    ],
    "word_count": 52,
}


async def run(
    translated_text: str,
    rubric_text: str,
    submission_id: str,
) -> dict[str, Any]:
    """
    Normalises submission content and parses rubric into structured JSON.
    """
    if settings.DEMO_MODE:
        return {**DEMO_OUTPUT, "submission_id": submission_id, "cleaned_content": translated_text}

    # ── Clean content ─────────────────────────────────────────────────────────
    cleaned = _clean_text(translated_text)
    word_count = len(cleaned.split())
    submission_type = _detect_type(cleaned)

    # ── Parse rubric via LLM ──────────────────────────────────────────────────
    rubric_prompt = f"""
You are a rubric parser. Convert the following teacher rubric into a JSON array.
Each element must have: "criterion" (string), "max_points" (integer), "description" (string).

Rubric text:
{rubric_text}

Return a JSON array only. Example:
[{{"criterion": "Argument Clarity", "max_points": 10, "description": "..."}}]
"""
    rubric_criteria = await llm_service.generate_json(rubric_prompt)
    if not isinstance(rubric_criteria, list):
        rubric_criteria = rubric_criteria.get("criteria", [])

    return {
        "submission_type": submission_type,
        "cleaned_content": cleaned,
        "rubric_criteria": rubric_criteria,
        "word_count": word_count,
        "submission_id": submission_id,
    }


def _clean_text(text: str) -> str:
    """Remove HTML tags, fix encoding artifacts, collapse whitespace."""
    text = re.sub(r"<[^>]+>", "", text)
    text = text.replace("\u00e2\u0080\u0099", "'").replace("\u00e2\u0080\u009c", '"').replace("\u00e2\u0080\u009d", '"')
    text = re.sub(r"\s+", " ", text).strip()
    return text


def _detect_type(text: str) -> str:
    """Heuristic submission type detection."""
    lowered = text.lower()
    if any(k in lowered for k in ["def ", "class ", "import ", "function ", "return ", "print("]):
        return "code"
    if re.search(r"\d+[\+\-\*/=]\d+", text) or "solve" in lowered or "equation" in lowered:
        return "math"
    if len(text.split()) < 100:
        return "short-answer"
    return "essay"

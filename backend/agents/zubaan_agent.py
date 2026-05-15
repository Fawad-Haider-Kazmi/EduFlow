"""
AGENT 1 — Zubaan Agent (Bidirectional Language Bridge)
Runs twice per pipeline: Direction 1 (input) and Direction 2 (output).
"""

import logging
from typing import Any

from config import settings
from services.llm_service import llm_service
from services.translation import detect_language, translate_to_english, translate_from_english

logger = logging.getLogger(__name__)

# ── Demo mock responses ────────────────────────────────────────────────────────
DEMO_INPUT_URDU = {
    "original_text": "یہ ایک طالب علم کا مضمون ہے جو پاکستان کی آزادی کے بارے میں ہے۔",
    "translated_text": "This is a student essay about Pakistan's independence.",
    "original_language": "urdu",
    "was_translated": True,
    "language_barrier_risk": True,
    "rubric_translated": "Criterion 1: Argument clarity (10 pts). Criterion 2: Use of evidence (10 pts).",
}

DEMO_INPUT_ENGLISH = {
    "original_text": "Pakistan gained independence on August 14, 1947...",
    "translated_text": "Pakistan gained independence on August 14, 1947...",
    "original_language": "english",
    "was_translated": False,
    "language_barrier_risk": False,
    "rubric_translated": None,
}


async def run_input(
    raw_text: str,
    rubric_text: str | None = None,
    demo_language: str = "english",
) -> dict[str, Any]:
    """
    Direction 1 — INPUT.
    Detects language, translates submission (and rubric) to English.
    Returns structured dict matching the Zubaan output spec.
    """
    if settings.DEMO_MODE:
        if demo_language == "urdu":
            return DEMO_INPUT_URDU
        return {**DEMO_INPUT_ENGLISH, "original_text": raw_text, "translated_text": raw_text}

    original_language = await detect_language(raw_text)
    translated_text = await translate_to_english(raw_text, original_language)

    # Language barrier risk: flag if submission is non-English
    language_barrier_risk = original_language not in ("english",)

    # If rubric is non-English, translate it too
    rubric_translated = None
    if rubric_text:
        rubric_lang = await detect_language(rubric_text)
        if rubric_lang != "english":
            rubric_translated = await translate_to_english(rubric_text, rubric_lang)

    # Roman Urdu check via LLM (no ISO code for detection)
    if original_language == "english" and _looks_like_roman_urdu(raw_text):
        original_language = "roman_urdu"
        language_barrier_risk = True

    return {
        "original_text": raw_text,
        "translated_text": translated_text,
        "original_language": original_language,
        "was_translated": original_language not in ("english", "roman_urdu"),
        "language_barrier_risk": language_barrier_risk,
        "rubric_translated": rubric_translated,
    }


async def run_output(
    english_feedback: str,
    original_language: str,
) -> dict[str, Any]:
    """
    Direction 2 — OUTPUT.
    Translates English feedback into the student's original language.
    For Roman Urdu, uses Gemini to transliterate rather than Google Translate.
    """
    if settings.DEMO_MODE:
        translated = f"[{original_language.upper()}] {english_feedback}"
        return {"english": english_feedback, "translated": translated, "language": original_language}

    if original_language == "roman_urdu":
        prompt = (
            f"Translate the following English student feedback into Roman Urdu "
            f"(Urdu words written in English letters, e.g. 'Aap ne bohat acha kaam kiya'). "
            f"Keep the tone warm and encouraging.\n\nFeedback:\n{english_feedback}"
        )
        translated = await llm_service.generate(prompt)
    else:
        translated = await translate_from_english(english_feedback, original_language)

    return {
        "english": english_feedback,
        "translated": translated,
        "language": original_language,
    }


def _looks_like_roman_urdu(text: str) -> bool:
    """Heuristic: common Roman Urdu words as signal."""
    markers = ["hai", "hain", "mein", "nahi", "kya", "aur", "bhi", "yeh", "woh", "kar", "tha"]
    words = text.lower().split()
    hits = sum(1 for w in words if w in markers)
    return hits / max(len(words), 1) > 0.08

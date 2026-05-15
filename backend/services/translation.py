"""
EduFlow — Google Cloud Translation Service wrapper.
Falls back to a no-op pass-through when credentials are not configured.
"""

import logging
from config import settings

logger = logging.getLogger(__name__)

LANGUAGE_MAP = {
    "urdu": "ur",
    "sindhi": "sd",
    "pashto": "ps",
    "punjabi": "pa",
    "english": "en",
    "roman_urdu": "en",  # Roman Urdu has no ISO code; we treat it as a special case
}


async def detect_language(text: str) -> str:
    """Returns a language label: english / urdu / roman_urdu / sindhi / pashto / mixed."""
    if not settings.GOOGLE_APPLICATION_CREDENTIALS:
        # Heuristic fallback: check for Urdu Unicode block
        urdu_chars = sum(1 for c in text if "\u0600" <= c <= "\u06FF")
        if urdu_chars / max(len(text), 1) > 0.3:
            return "urdu"
        return "english"
    try:
        from google.cloud import translate_v2 as translate
        client = translate.Client()
        result = client.detect_language(text)
        lang = result["language"]
        reverse = {v: k for k, v in LANGUAGE_MAP.items()}
        return reverse.get(lang, "english")
    except Exception as e:
        logger.warning(f"Language detection failed: {e}")
        return "english"


async def translate_to_english(text: str, source_language: str) -> str:
    """Translates text to English. Returns original text if already English."""
    if source_language in ("english", "roman_urdu"):
        return text
    if not settings.GOOGLE_APPLICATION_CREDENTIALS:
        logger.warning("Translation credentials not set — returning original text.")
        return text
    try:
        from google.cloud import translate_v2 as translate
        client = translate.Client()
        src_code = LANGUAGE_MAP.get(source_language, "ur")
        result = client.translate(text, source_language=src_code, target_language="en")
        return result["translatedText"]
    except Exception as e:
        logger.error(f"Translation failed: {e}")
        return text


async def translate_from_english(text: str, target_language: str) -> str:
    """Translates English text to the target language."""
    if target_language == "english":
        return text
    if target_language == "roman_urdu":
        # Google Translate doesn't support Roman Urdu natively;
        # we prompt Gemini to transliterate in the feedback agent instead.
        return text
    if not settings.GOOGLE_APPLICATION_CREDENTIALS:
        logger.warning("Translation credentials not set — returning English text.")
        return text
    try:
        from google.cloud import translate_v2 as translate
        client = translate.Client()
        tgt_code = LANGUAGE_MAP.get(target_language, "ur")
        result = client.translate(text, source_language="en", target_language=tgt_code)
        return result["translatedText"]
    except Exception as e:
        logger.error(f"Translation failed: {e}")
        return text

"""
EduFlow — Gemini LLM Service
Wraps google-generativeai with JSON parsing, retry logic, and DEMO_MODE mock returns.
"""

import json
import asyncio
import logging
from typing import Any

import google.generativeai as genai

from config import settings

logger = logging.getLogger(__name__)

genai.configure(api_key=settings.GEMINI_API_KEY)


class LLMService:
    def __init__(self):
        self.model = genai.GenerativeModel(settings.GEMINI_MODEL)

    async def generate(self, prompt: str) -> str:
        """Raw text generation — runs in a thread to avoid blocking the event loop."""
        loop = asyncio.get_event_loop()
        response = await loop.run_in_executor(
            None, lambda: self.model.generate_content(prompt)
        )
        return response.text

    async def generate_json(self, prompt: str) -> dict[str, Any]:
        """
        Generate content expecting a JSON response.
        Strips markdown fences if the model wraps output in ```json ... ```.
        Retries once on parse failure.
        """
        for attempt in range(2):
            raw = await self.generate(prompt + "\n\nRespond with valid JSON only. No markdown fences.")
            raw = raw.strip().removeprefix("```json").removeprefix("```").removesuffix("```").strip()
            try:
                return json.loads(raw)
            except json.JSONDecodeError as e:
                if attempt == 0:
                    logger.warning(f"JSON parse failed (attempt 1), retrying. Error: {e}")
                    continue
                logger.error(f"JSON parse failed after 2 attempts: {e}\nRaw: {raw[:500]}")
                raise ValueError(f"LLM returned invalid JSON: {e}") from e
        return {}


# Singleton
llm_service = LLMService()

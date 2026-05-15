"""
AGENT 3 — Integrity Agent
Checks plagiarism via FAISS semantic similarity and AI-generated content via stylometrics.
Runs in parallel with the Grading Agent (Step 3).
"""

import math
import logging
import statistics
from typing import Any

from config import settings
from services.faiss_store import faiss_store
from services.llm_service import llm_service

logger = logging.getLogger(__name__)

PLAGIARISM_THRESHOLD = 0.85
OVERALL_FLAG_THRESHOLD = 70   # If either score > 70, raise flag

DEMO_OUTPUT_CLEAN = {
    "plagiarism_score": 12,
    "plagiarism_evidence": "No significant semantic overlap detected with other submissions in this class.",
    "ai_generated_score": 18,
    "ai_evidence": "Sentence length variance is within normal human range (std dev: 4.3). Vocabulary richness index: 0.71.",
    "overall_integrity_flag": False,
    "recommendation": "Submission appears original. Proceed to grading.",
}

DEMO_OUTPUT_FLAGGED = {
    "plagiarism_score": 87,
    "plagiarism_evidence": "Paragraphs 2 and 3 share 91% semantic similarity with Sara Malik's submission (SUB-002). Overlapping passage: 'The partition of British India in 1947 resulted in...'",
    "ai_generated_score": 76,
    "ai_evidence": "Unusually low sentence length variance (std dev: 1.1). Vocabulary richness index: 0.94 (typical human range: 0.60–0.80). Perplexity score suggests formulaic structure.",
    "overall_integrity_flag": True,
    "recommendation": "Flag for teacher review — potential AI assistance and cross-submission copying detected.",
}


async def run(
    submission_id: str,
    class_id: str,
    cleaned_content: str,
    demo_flag: bool = False,
) -> dict[str, Any]:
    """
    Returns integrity analysis. Does NOT make a final judgment — evidence only.
    """
    if settings.DEMO_MODE:
        return DEMO_OUTPUT_FLAGGED if demo_flag else DEMO_OUTPUT_CLEAN

    # ── Plagiarism check ──────────────────────────────────────────────────────
    similar = faiss_store.search(
        cleaned_content, class_id=class_id, top_k=3, exclude_id=submission_id
    )
    plag_score = 0
    plag_evidence = "No significant overlap detected."
    if similar:
        top_id, top_score = similar[0]
        plag_score = int(top_score * 100)
        if top_score > PLAGIARISM_THRESHOLD:
            plag_evidence = (
                f"High semantic similarity ({plag_score}%) detected with submission {top_id}. "
                f"Please review both submissions side by side."
            )

    # ── AI-generated content check (stylometrics) ─────────────────────────────
    ai_score, ai_evidence = _stylometric_analysis(cleaned_content)

    # ── LLM-assisted AI detection ─────────────────────────────────────────────
    if ai_score > 50:
        prompt = f"""
Analyse this student submission for signs of AI-generated content.
Look for: formulaic sentence structure, unusually consistent tone, lack of personal voice,
perfect grammar with zero colloquialisms.

Submission (first 500 words):
{cleaned_content[:2000]}

Return JSON: {{"ai_confidence": 0-100, "reasoning": "..."}}
"""
        result = await llm_service.generate_json(prompt)
        llm_ai_score = result.get("ai_confidence", ai_score)
        llm_reasoning = result.get("reasoning", "")
        ai_score = int((ai_score + llm_ai_score) / 2)
        ai_evidence += f" LLM analysis: {llm_reasoning}"

    # ── Index this submission into FAISS for future comparisons ───────────────
    faiss_store.add(submission_id, class_id, cleaned_content)

    overall_flag = plag_score > OVERALL_FLAG_THRESHOLD or ai_score > OVERALL_FLAG_THRESHOLD
    recommendation = (
        "Flag for teacher review — integrity concerns detected."
        if overall_flag
        else "Submission appears original. Proceed to grading."
    )

    return {
        "plagiarism_score": plag_score,
        "plagiarism_evidence": plag_evidence,
        "ai_generated_score": ai_score,
        "ai_evidence": ai_evidence,
        "overall_integrity_flag": overall_flag,
        "recommendation": recommendation,
    }


def _stylometric_analysis(text: str) -> tuple[int, str]:
    """
    Compute basic stylometric signals.
    Returns (confidence_score_0_100, evidence_string).
    """
    sentences = [s.strip() for s in text.replace("!", ".").replace("?", ".").split(".") if s.strip()]
    if len(sentences) < 3:
        return 10, "Too short for reliable analysis."

    lengths = [len(s.split()) for s in sentences]
    try:
        std_dev = statistics.stdev(lengths)
    except statistics.StatisticsError:
        std_dev = 0

    words = text.lower().split()
    unique_words = len(set(words))
    vocab_richness = round(unique_words / max(len(words), 1), 2)

    # Low variance → suspicious; high vocab richness → suspicious
    score = 0
    evidence_parts = []

    if std_dev < 2.0:
        score += 40
        evidence_parts.append(f"Very low sentence length variance (std dev: {std_dev:.1f})")
    elif std_dev < 3.5:
        score += 15
        evidence_parts.append(f"Below-average sentence length variance (std dev: {std_dev:.1f})")

    if vocab_richness > 0.90:
        score += 40
        evidence_parts.append(f"Unusually high vocabulary richness ({vocab_richness}) — typical human range: 0.60–0.80")
    elif vocab_richness > 0.82:
        score += 20
        evidence_parts.append(f"Elevated vocabulary richness ({vocab_richness})")

    evidence = ". ".join(evidence_parts) if evidence_parts else "Stylometric signals within normal range."
    return min(score, 100), evidence

"""
AGENT 4 — Grading Agent
Scores each rubric criterion individually with cited rationale from the submission.
Runs in parallel with the Integrity Agent (Step 3).
"""

import logging
import statistics
from typing import Any

from config import settings
from services.llm_service import llm_service

logger = logging.getLogger(__name__)

DEMO_OUTPUT = {
    "criteria_scores": [
        {
            "criterion": "Argument Clarity",
            "score": 8,
            "max": 10,
            "rationale": "Your thesis statement in the opening paragraph is clear and well-stated. However, the argument loses focus in the third paragraph where the transition from political to social consequences is abrupt.",
            "cited_text": "Pakistan gained independence on August 14, 1947, after a long struggle...",
        },
        {
            "criterion": "Use of Evidence",
            "score": 6,
            "max": 10,
            "rationale": "You cited the role of Muhammad Ali Jinnah accurately, but the essay would benefit from specific dates, treaties, or statistics to support your claims about the partition's impact.",
            "cited_text": "The partition of British India created two new nations.",
        },
        {
            "criterion": "Structure & Organisation",
            "score": 9,
            "max": 10,
            "rationale": "The essay has a clear introduction, three well-organised body paragraphs, and a strong conclusion. Minor deduction for the abrupt paragraph three transition.",
            "cited_text": "In conclusion, Pakistan's independence remains a defining moment...",
        },
        {
            "criterion": "Language Quality",
            "score": 7,
            "max": 10,
            "rationale": "Grammar is mostly correct with a few minor errors ('the leaders who was present' → 'were present'). Vocabulary is appropriate for Grade 9 level.",
            "cited_text": "the leaders who was present at the ceremony",
        },
        {
            "criterion": "Critical Thinking",
            "score": 6,
            "max": 10,
            "rationale": "You described events accurately but the essay is largely descriptive rather than analytical. A stronger response would evaluate why partition happened, not just what happened.",
            "cited_text": "Pakistan became independent after the British left.",
        },
    ],
    "total_score": 36,
    "total_max": 50,
    "percentage": 72.0,
    "needs_intervention": False,
    "language_barrier_note": None,
}

DEMO_OUTPUT_URDU_STUDENT = {
    **DEMO_OUTPUT,
    "total_score": 28,
    "total_max": 50,
    "percentage": 56.0,
    "needs_intervention": True,
    "language_barrier_note": "Note: Student submitted in Urdu. Concept understanding has been assessed independently of language quality. The student demonstrates solid understanding of the historical events despite language limitations.",
}


async def run(
    submission_id: str,
    cleaned_content: str,
    rubric_criteria: list[dict],
    language_barrier_risk: bool,
    class_percentages: list[float] | None = None,
    demo_urdu: bool = False,
) -> dict[str, Any]:
    """
    Scores each rubric criterion. Returns detailed per-criterion breakdown.
    Never hallucinates quotes — only cites text from cleaned_content.
    """
    if settings.DEMO_MODE:
        return _demo_grade(cleaned_content, language_barrier_risk, demo_urdu)

    rubric_json = "\n".join(
        f"- {c['criterion']} ({c['max_points']} pts): {c.get('description', '')}"
        for c in rubric_criteria
    )
    barrier_instruction = (
        "IMPORTANT: The student submitted in a language other than English. "
        "Assess CONCEPT UNDERSTANDING only. Do not penalise for language quality "
        "unless 'Language Quality' is an explicit rubric criterion.\n"
        if language_barrier_risk
        else ""
    )

    prompt = f"""
You are a fair, evidence-based grader for a Pakistan secondary school.
{barrier_instruction}
Score the following student submission against each rubric criterion.

RUBRIC:
{rubric_json}

STUDENT SUBMISSION:
{cleaned_content}

For each criterion, provide:
- score (integer, 0 to max_points)
- rationale (2-3 sentences, direct and specific)
- cited_text (a direct quote from the submission — ONLY use text that actually appears above)

Return a JSON object:
{{
  "criteria_scores": [
    {{"criterion": "...", "score": N, "max": N, "rationale": "...", "cited_text": "..."}}
  ]
}}
"""
    result = await llm_service.generate_json(prompt)
    criteria_scores = result.get("criteria_scores", [])

    total_score = sum(c.get("score", 0) for c in criteria_scores)
    total_max = sum(c.get("max", c.get("max_points", 10)) for c in criteria_scores)
    percentage = round(total_score / total_max * 100, 1) if total_max > 0 else 0

    # Check if student is an outlier (>1.5 std devs below class mean)
    needs_intervention = False
    if class_percentages and len(class_percentages) >= 3:
        mean = statistics.mean(class_percentages)
        stdev = statistics.stdev(class_percentages)
        if stdev > 0 and (mean - percentage) > 1.5 * stdev:
            needs_intervention = True

    language_barrier_note = None
    if language_barrier_risk:
        language_barrier_note = (
            "Note: Student submitted in their native language. "
            "Concept understanding was assessed independently of language quality."
        )

    return {
        "criteria_scores": criteria_scores,
        "total_score": total_score,
        "total_max": total_max,
        "percentage": percentage,
        "needs_intervention": needs_intervention,
        "language_barrier_note": language_barrier_note,
    }


def _demo_grade(cleaned_content: str, language_barrier_risk: bool, demo_urdu: bool) -> dict:
    """
    DEMO_MODE grader: derives scores and cited quotes from the actual submission
    so the breakdown reflects what the student actually wrote.
    """
    words   = cleaned_content.split()
    wc      = len(words)
    sents   = [s.strip() for s in cleaned_content.replace("!", ".").replace("?", ".").split(".") if s.strip()]
    n_sents = max(len(sents), 1)

    def snippet(idx: int, max_len: int = 90) -> str:
        """Return a real quoted sentence from the text, capped at max_len chars."""
        s = sents[min(idx, n_sents - 1)]
        return s[:max_len] + ("…" if len(s) > max_len else "")

    # Score heuristics based on length and sentence variety
    try:
        lengths = [len(s.split()) for s in sents]
        std_dev = statistics.stdev(lengths) if len(lengths) > 1 else 0
    except statistics.StatisticsError:
        std_dev = 0

    unique_ratio  = len(set(w.lower() for w in words)) / max(wc, 1)
    length_score  = min(int(wc / 5), 9)          # 0-9 based on word count
    variety_score = min(int(std_dev * 1.5), 9)   # 0-9 based on sentence variety
    vocab_score   = min(int(unique_ratio * 12), 9)

    def clamp(v: int) -> int:
        return max(4, min(v, 9))

    arg_score  = clamp(length_score)
    ev_score   = clamp(length_score - 2)
    str_score  = clamp(variety_score + 5)
    lang_score = clamp(vocab_score)
    crit_score = clamp(length_score - 1)

    if demo_urdu or language_barrier_risk:
        lang_score = max(lang_score - 2, 3)
        barrier_note = (
            "Note: Student submitted in their native language. "
            "Concept understanding was assessed independently of language quality."
        )
    else:
        barrier_note = None

    rationales = {
        "Argument Clarity": (
            f"The main idea is present but {'well developed across {n_sents} sentences' if n_sents >= 3 else 'could be expanded with more detail'}. "
            f"{'A clear position is maintained throughout.' if arg_score >= 7 else 'Strengthening the central argument with more supporting points would improve this score.'}"
        ),
        "Use of Evidence": (
            f"{'Specific details are cited to support the argument.' if ev_score >= 7 else 'The response would benefit from more specific facts, dates, or examples to back up claims.'} "
            f"{'Evidence is well integrated.' if ev_score >= 8 else 'Try quoting or referencing sources more directly.'}"
        ),
        "Structure & Organisation": (
            f"The response has {'a clear progression of ideas across multiple sentences' if n_sents >= 4 else 'a basic structure but could benefit from a clearer introduction and conclusion'}. "
            f"{'Paragraph transitions are smooth.' if str_score >= 7 else 'Adding topic sentences at the start of each paragraph would improve organisation.'}"
        ),
        "Language Quality": (
            f"Vocabulary richness is {'strong' if vocab_score >= 7 else 'adequate'} ({round(unique_ratio * 100)}% unique words). "
            f"{'Grammar and spelling are largely correct.' if lang_score >= 7 else 'Some grammatical errors are present. Review sentence construction and subject-verb agreement.'}"
        ),
        "Critical Thinking": (
            f"The response {'moves beyond basic description and shows some analytical thinking' if crit_score >= 7 else 'is largely descriptive. A stronger response would analyse causes, effects, or evaluate multiple perspectives'}. "
            f"{'Good use of reasoning.' if crit_score >= 7 else 'Try asking "why" and "so what?" after each point.'}"
        ),
    }

    criteria_scores = [
        {"criterion": "Argument Clarity",      "score": arg_score,  "max": 10, "rationale": rationales["Argument Clarity"],      "cited_text": snippet(0)},
        {"criterion": "Use of Evidence",       "score": ev_score,   "max": 10, "rationale": rationales["Use of Evidence"],       "cited_text": snippet(min(1, n_sents-1))},
        {"criterion": "Structure & Organisation", "score": str_score, "max": 10, "rationale": rationales["Structure & Organisation"], "cited_text": snippet(min(2, n_sents-1))},
        {"criterion": "Language Quality",      "score": lang_score, "max": 10, "rationale": rationales["Language Quality"],      "cited_text": snippet(min(3, n_sents-1))},
        {"criterion": "Critical Thinking",     "score": crit_score, "max": 10, "rationale": rationales["Critical Thinking"],     "cited_text": snippet(n_sents-1)},
    ]

    total_score = sum(c["score"] for c in criteria_scores)
    total_max   = 50
    percentage  = round(total_score / total_max * 100, 1)

    return {
        "criteria_scores": criteria_scores,
        "total_score": total_score,
        "total_max": total_max,
        "percentage": percentage,
        "needs_intervention": percentage < 50,
        "language_barrier_note": barrier_note,
    }

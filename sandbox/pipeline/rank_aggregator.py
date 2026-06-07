"""
Rank aggregator for the TalentMind AI ranking pipeline.

Combines semantic and behavioral scores, reranks the top-10 with
availability/engagement boosts, enforces strict monotonic decreasing
scores, rescales to [0.40, 0.95], and generates per-candidate reasoning.

This is the final stage before output.
"""

from __future__ import annotations

import math
from typing import Any, Dict, List, Optional, Set

import numpy as np

from sandbox.pipeline.semantic_scorer import compute_semantic_score
from sandbox.pipeline.behavioral_scorer import compute_behavioral_score

# ──────────────────────────────────────────────────────────────────────
# Constants
# ──────────────────────────────────────────────────────────────────────

SEMANTIC_WEIGHT = 0.62
BEHAVIORAL_WEIGHT = 0.38

SCORE_MIN = 0.40
SCORE_MAX = 0.95


def aggregate_and_rank(
    candidates: List[Dict[str, Any]],
    jd_profile: Dict[str, Any],
    tfidf_scores: np.ndarray,
    top_n: int = 100,
) -> List[Dict[str, Any]]:
    """
    Score, sort, rerank and format the final ranked shortlist.

    Parameters
    ----------
    candidates : list[dict]
        Normalised candidate dicts (honeypot flag already set).
    jd_profile : dict
        Parsed JD profile.
    tfidf_scores : np.ndarray
        Pre-computed TF-IDF overlap scores, same order as candidates.
    top_n : int
        Number of candidates to return (default 100).

    Returns
    -------
    list[dict] — top_n candidates, each with:
        rank, candidate_id, _score, semantic_score, behavioral_score,
        reasoning, and all original candidate fields.
    """
    scored: List[Dict[str, Any]] = []

    for i, cand in enumerate(candidates):
        # Skip honeypots
        if cand.get("is_honeypot", False):
            continue

        tfidf = float(tfidf_scores[i]) if i < len(tfidf_scores) else 0.0
        sem = compute_semantic_score(cand, jd_profile, tfidf)
        beh, beh_breakdown = compute_behavioral_score(cand.get("signals") or {})

        composite = SEMANTIC_WEIGHT * sem + BEHAVIORAL_WEIGHT * beh

        entry = dict(cand)
        entry["semantic_score"] = round(sem, 4)
        entry["behavioral_score"] = round(beh, 4)
        entry["_score"] = round(composite, 4)
        entry["_beh_breakdown"] = beh_breakdown
        scored.append(entry)

    # ── Sort descending ──────────────────────────────────────────────
    scored.sort(key=lambda x: x["_score"], reverse=True)

    # Take top_n
    shortlist = scored[:top_n]

    # ── Rerank top 10 ────────────────────────────────────────────────
    shortlist = _rerank_top10(shortlist)

    # Re-sort after reranking
    shortlist.sort(key=lambda x: x["_score"], reverse=True)

    # ── Enforce monotonic scores ─────────────────────────────────────
    shortlist = _enforce_monotonic_scores(shortlist)

    # ── Rescale to [0.40, 0.95] ──────────────────────────────────────
    shortlist = _rescale_scores(shortlist)

    # ── Generate reasoning ───────────────────────────────────────────
    for rank_idx, entry in enumerate(shortlist, 1):
        entry["rank"] = rank_idx
        entry["reasoning"] = _generate_reasoning(
            entry, entry.get("_beh_breakdown", {}), jd_profile, rank_idx
        )

    return shortlist


# ──────────────────────────────────────────────────────────────────────
# Rerank top 10
# ──────────────────────────────────────────────────────────────────────

def _rerank_top10(shortlist: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Apply availability/engagement boosts and penalties to positions 1-10.

    Boosts:
        open_to_work        +0.02
        rr ≥ 0.7            +0.03
        notice ≤ 30d        +0.02
        notice ≤ 60d        +0.01
        github ≥ 70         +0.02
        verified contacts   +0.01

    Penalties:
        icr < 0.3           -0.03
        oar < 0.3           -0.02
    """
    for entry in shortlist[:10]:
        signals = entry.get("signals") or {}
        boost = 0.0

        # Open to work
        if signals.get("open_to_work_flag", False):
            boost += 0.02

        # Recruiter response rate ≥ 0.7
        rr = _safe_float(signals.get("recruiter_response_rate"))
        if rr >= 0.7:
            boost += 0.03

        # Notice period (if present)
        notice = _safe_float(signals.get("notice_period_days"))
        if notice is not None and notice <= 30:
            boost += 0.02
        elif notice is not None and notice <= 60:
            boost += 0.01

        # GitHub activity ≥ 70
        github = _safe_float(signals.get("github_activity_score"))
        if github >= 70:
            boost += 0.02

        # Verified contacts
        if signals.get("verified_email", False) or signals.get("verified_phone", False):
            boost += 0.01

        # Penalties
        icr = _safe_float(signals.get("interview_completion_rate"))
        if icr < 0.3:
            boost -= 0.03

        oar = _safe_float(signals.get("offer_acceptance_rate"))
        if oar < 0.3:
            boost -= 0.02

        entry["_score"] = round(entry["_score"] + boost, 4)

    return shortlist


# ──────────────────────────────────────────────────────────────────────
# Monotonicity enforcement
# ──────────────────────────────────────────────────────────────────────

def _enforce_monotonic_scores(
    shortlist: List[Dict[str, Any]],
    epsilon: float = 0.0001,
) -> List[Dict[str, Any]]:
    """
    Ensure _score is strictly decreasing by at least epsilon per rank.

    If a later candidate has a score ≥ the previous one, it is clamped
    to previous - epsilon.
    """
    if not shortlist:
        return shortlist

    for i in range(1, len(shortlist)):
        if shortlist[i]["_score"] >= shortlist[i - 1]["_score"]:
            shortlist[i]["_score"] = round(
                shortlist[i - 1]["_score"] - epsilon, 6
            )

    return shortlist


# ──────────────────────────────────────────────────────────────────────
# Score rescaling
# ──────────────────────────────────────────────────────────────────────

def _rescale_scores(shortlist: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Linearly rescale _score to [SCORE_MIN, SCORE_MAX]."""
    if not shortlist:
        return shortlist

    raw_scores = [e["_score"] for e in shortlist]
    raw_min = min(raw_scores)
    raw_max = max(raw_scores)
    raw_range = raw_max - raw_min

    if raw_range < 1e-9:
        # All scores identical — assign midpoint
        mid = (SCORE_MIN + SCORE_MAX) / 2
        for e in shortlist:
            e["_score"] = round(mid, 4)
    else:
        for e in shortlist:
            normalised = (e["_score"] - raw_min) / raw_range
            e["_score"] = round(
                SCORE_MIN + normalised * (SCORE_MAX - SCORE_MIN), 4
            )

    # Re-enforce monotonicity after rescaling
    for i in range(1, len(shortlist)):
        if shortlist[i]["_score"] >= shortlist[i - 1]["_score"]:
            shortlist[i]["_score"] = round(shortlist[i - 1]["_score"] - 0.0001, 4)

    return shortlist


# ──────────────────────────────────────────────────────────────────────
# Reasoning generator
# ──────────────────────────────────────────────────────────────────────

def _generate_reasoning(
    candidate: Dict[str, Any],
    beh_breakdown: Dict[str, float],
    jd_profile: Dict[str, Any],
    rank: int,
) -> str:
    """
    Generate a human-readable reasoning string for a ranked candidate.

    Includes: title + years, matched skills, github score, open_to_work,
    concern sentence for gaps/low experience/low response rate.
    """
    parts: List[str] = []

    title = candidate.get("current_title", "Unknown")
    years = candidate.get("years_experience", 0)
    parts.append(f"#{rank}: {title} with {years:.0f}y experience.")

    # Matched skills
    cand_skills = candidate.get("skills_set", set())
    jd_skills = (
        jd_profile.get("required_skills", set())
        | jd_profile.get("preferred_skills", set())
    )
    matched = cand_skills & jd_skills
    if matched:
        top_matched = sorted(matched)[:8]
        parts.append(f"Matched skills: {', '.join(top_matched)}.")
    else:
        parts.append("No direct skill matches with JD requirements.")

    # GitHub
    signals = candidate.get("signals") or {}
    github = _safe_float(signals.get("github_activity_score"))
    if github > 0:
        parts.append(f"GitHub activity: {github:.0f}/100.")

    # Open to work
    if signals.get("open_to_work_flag", False):
        parts.append("Open to new opportunities.")

    # Concerns
    concerns: List[str] = []
    min_years = jd_profile.get("min_years")
    if min_years and years < min_years * 0.6:
        concerns.append(f"below JD minimum experience ({years:.0f}y vs {min_years:.0f}y required)")

    rr = _safe_float(signals.get("recruiter_response_rate"))
    if rr < 0.3:
        concerns.append(f"low recruiter response rate ({rr:.0%})")

    icr = _safe_float(signals.get("interview_completion_rate"))
    if icr < 0.3:
        concerns.append(f"low interview completion rate ({icr:.0%})")

    if concerns:
        parts.append(f"Concerns: {'; '.join(concerns)}.")

    return " ".join(parts)


# ──────────────────────────────────────────────────────────────────────
# Serialisation helper
# ──────────────────────────────────────────────────────────────────────

def make_serializable(obj: Any) -> Any:
    """
    Recursively convert numpy types, sets, and other non-JSON types
    to JSON-serializable Python primitives.
    """
    if isinstance(obj, dict):
        return {k: make_serializable(v) for k, v in obj.items()}
    if isinstance(obj, (list, tuple)):
        return [make_serializable(v) for v in obj]
    if isinstance(obj, set):
        return sorted(make_serializable(v) for v in obj)
    if isinstance(obj, (np.integer,)):
        return int(obj)
    if isinstance(obj, (np.floating,)):
        return float(obj)
    if isinstance(obj, np.ndarray):
        return obj.tolist()
    if isinstance(obj, float) and (math.isnan(obj) or math.isinf(obj)):
        return 0.0
    return obj


def _safe_float(val: Any, default: float = 0.0) -> float:
    if val is None:
        return default
    try:
        return float(val)
    except (ValueError, TypeError):
        return default

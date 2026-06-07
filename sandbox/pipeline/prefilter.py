"""
Pre-filter stage for the TalentMind AI ranking pipeline.

Performs O(n) JD-adaptive triage of the full candidate pool into three
buckets — definite, possible, and discarded — before expensive scoring.

This dramatically reduces the candidate set for large pools (100k+) while
ensuring no strong candidates are dropped via a safety-net fallback.
"""

from __future__ import annotations

from typing import Any, Dict, List, Tuple

from sandbox.utils.text_utils import tokenize


def prefilter_candidates(
    candidates: List[Dict[str, Any]],
    jd_profile: Dict[str, Any],
) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]], int]:
    """
    JD-adaptive pre-filter: split candidates into definite / possible / discard.

    Parameters
    ----------
    candidates : list[dict]
        Normalised candidate dicts.
    jd_profile : dict
        Parsed JD profile from jd_parser.parse_job_description.

    Returns
    -------
    (definite, possible, disqualified_count)
        definite  – candidates with title-token overlap (high priority)
        possible  – candidates with skill overlap but no title match
        disqualified_count – number of candidates discarded

    Notes
    -----
    Safety net: if survivors < 5% of total, falls back to returning all
    candidates as possible (avoids over-aggressive filtering on unusual JDs).
    """
    total = len(candidates)
    if total == 0:
        return [], [], 0

    # ── Extract JD title keywords and skill keywords ─────────────────
    title_keywords = jd_profile.get("title_keywords") or set()
    jd_skills = (
        jd_profile.get("required_skills", set())
        | jd_profile.get("preferred_skills", set())
    )

    # Build a lowercase set of JD skill tokens for fast matching
    jd_skill_tokens: set[str] = set()
    for skill in jd_skills:
        jd_skill_tokens |= set(skill.lower().split())

    definite: List[Dict[str, Any]] = []
    possible: List[Dict[str, Any]] = []
    disqualified = 0

    for cand in candidates:
        # Skip honeypots
        if cand.get("is_honeypot", False):
            disqualified += 1
            continue

        # Tokenize candidate title
        cand_title_tokens = set(tokenize(cand.get("current_title", "")))
        cand_skills = cand.get("skills_set") or set()
        cand_skill_tokens: set[str] = set()
        for skill in cand_skills:
            cand_skill_tokens |= set(skill.lower().split())

        # Check title overlap
        title_overlap = cand_title_tokens & title_keywords
        if title_overlap:
            definite.append(cand)
            continue

        # Check skill overlap
        skill_overlap = cand_skill_tokens & jd_skill_tokens
        if len(skill_overlap) >= 1:
            possible.append(cand)
            continue

        # Also check raw skill set against JD skills
        raw_skill_overlap = cand_skills & jd_skills
        if raw_skill_overlap:
            possible.append(cand)
            continue

        disqualified += 1

    survivors = len(definite) + len(possible)

    # ── Safety net: if too aggressive, fall back ─────────────────────
    min_survivors = max(1, int(total * 0.05))
    if survivors < min_survivors:
        # Return all non-honeypot candidates as possible
        all_valid = [c for c in candidates if not c.get("is_honeypot", False)]
        return [], all_valid, total - len(all_valid)

    return definite, possible, disqualified

"""
Candidate normalizer for the TalentMind AI ranking pipeline.

Transforms raw JSONL candidate dicts (with nested profile, skills, education,
career_history, and redrob_signals) into a flat profile dict suitable for
downstream scoring.

Handles missing fields, None values, and malformed records gracefully.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional, Set

from sandbox.utils.text_utils import compute_seniority_level, extract_skills_from_text


def normalize_candidate(raw: Dict[str, Any]) -> Dict[str, Any]:
    """
    Normalise a raw JSONL candidate record into a flat profile dict.

    Parameters
    ----------
    raw : dict
        Raw candidate record from JSONL. Expected nested structure:
        candidate_id, profile{}, skills[], education{}, career_history[],
        redrob_signals{}.

    Returns
    -------
    dict with keys:
        candidate_id, name, current_title, years_experience, skills_set,
        seniority_level, education_level, signals, is_honeypot,
        honeypot_reason, _raw
    """
    if not isinstance(raw, dict):
        raise TypeError(
            f"normalize_candidate expected dict, got {type(raw).__name__}: {repr(raw)[:80]}"
        )
    profile = raw.get("profile") or {}
    skills_list_raw = raw.get("skills") or []
    education_raw = raw.get("education")
    career_history: List[Dict[str, Any]] = raw.get("career_history") or []
    signals: Dict[str, Any] = raw.get("redrob_signals") or {}

    # ── Normalise education to a single dict ─────────────────────────
    # Accepts: dict, list of dicts, or None
    if isinstance(education_raw, list):
        # Array of education entries — pick the highest-level one
        education = _best_education(education_raw)
    elif isinstance(education_raw, dict):
        education = education_raw
    else:
        education = {}

    # ── Basic fields ─────────────────────────────────────────────────
    candidate_id: str = str(raw.get("candidate_id", "unknown"))

    # profile might also be a list in some schemas
    if isinstance(profile, list):
        profile = profile[0] if profile else {}
    if not isinstance(profile, dict):
        profile = {}

    name: str = profile.get("anonymized_name", "") or profile.get("name", "") or ""
    current_title: str = profile.get("current_title", "") or profile.get("title", "") or ""
    years_experience: float = _safe_float(
        profile.get("years_of_experience") or profile.get("years_experience"),
        default=0.0,
    )
    summary: str = profile.get("summary", "") or profile.get("bio", "") or ""
    headline: str = profile.get("headline", "") or ""

    # ── Skills ───────────────────────────────────────────────────────
    skills_set: Set[str] = set()
    for sk in skills_list_raw:
        if isinstance(sk, dict):
            name_raw = (sk.get("name") or sk.get("skill") or "").strip().lower()
        elif isinstance(sk, str):
            name_raw = sk.strip().lower()
        else:
            continue
        if name_raw:
            skills_set.add(name_raw)

    # Also extract skills from summary / headline for coverage
    skills_set |= extract_skills_from_text(summary)
    skills_set |= extract_skills_from_text(headline)
    skills_set |= extract_skills_from_text(current_title)

    # ── Seniority ────────────────────────────────────────────────────
    seniority_level: int = compute_seniority_level(years_experience, current_title)

    # ── Education level (0-4) ────────────────────────────────────────
    education_level: int = _compute_education_level(education)

    # ── Honeypot detection is deferred to honeypot_detector module ──
    # We set placeholders here; the normalizer doesn't decide honeypot status.
    return {
        "candidate_id": candidate_id,
        "name": name,
        "current_title": current_title,
        "years_experience": years_experience,
        "summary": summary,
        "headline": headline,
        "skills_set": skills_set,
        "skills_raw": skills_list_raw,
        "seniority_level": seniority_level,
        "education_level": education_level,
        "education": education,
        "career_history": career_history,
        "signals": signals,
        "is_honeypot": False,
        "honeypot_reason": "",
        "_raw": raw,
    }


# ──────────────────────────────────────────────────────────────────────
# Helpers
# ──────────────────────────────────────────────────────────────────────

_DEGREE_MAP = {
    "phd": 4, "ph.d": 4, "doctorate": 4, "doctoral": 4,
    "master": 3, "msc": 3, "m.sc": 3, "mba": 3, "m.s.": 3,
    "ms ": 3, "ma ": 3, "m.a.": 3, "meng": 3, "m.eng": 3,
    "bachelor": 2, "bsc": 2, "b.sc": 2, "b.s.": 2, "ba ": 2,
    "b.a.": 2, "beng": 2, "b.eng": 2, "b.tech": 2, "btech": 2,
    "associate": 1, "diploma": 1, "certificate": 1, "bootcamp": 1,
}


def _best_education(edu_list: List[Any]) -> Dict[str, Any]:
    """Pick the highest-level education entry from a list of dicts."""
    best: Dict[str, Any] = {}
    best_level = -1
    for entry in edu_list:
        if not isinstance(entry, dict):
            continue
        level = _compute_education_level(entry)
        if level > best_level:
            best_level = level
            best = entry
    return best


def _compute_education_level(edu: Any) -> int:
    """Map education info to a 0-4 integer level."""
    if not edu or not isinstance(edu, dict):
        return 0

    degree = (edu.get("degree") or edu.get("degree_type") or "").lower()
    for keyword, level in _DEGREE_MAP.items():
        if keyword in degree:
            return level

    # If degree field is present but unrecognised, give baseline credit
    if degree:
        return 1
    return 0


def _safe_float(val: Any, default: float = 0.0) -> float:
    """Safely convert a value to float."""
    if val is None:
        return default
    try:
        return float(val)
    except (ValueError, TypeError):
        return default

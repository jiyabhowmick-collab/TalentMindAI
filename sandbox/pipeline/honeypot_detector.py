"""
Honeypot / bot / bad-data detector for the TalentMind AI ranking pipeline.

Applies 12 heuristic rules to flag synthetic, fraudulent, or corrupted
candidate records. Each rule returns a human-readable reason string when
triggered.

All detection is rule-based — no ML models or external lookups.
"""

from __future__ import annotations

import re
from typing import Any, Dict, List, Tuple


def is_honeypot(candidate: Dict[str, Any]) -> Tuple[bool, str]:
    """
    Check whether a normalised candidate record is a honeypot / bot / bad data.

    Parameters
    ----------
    candidate : dict
        Normalised candidate dict (output of candidate_normalizer.normalize_candidate).

    Returns
    -------
    (is_flagged, reason) : (bool, str)
        True + reason string if any rule fires, else (False, "").
    """
    for rule_fn in _RULES:
        flagged, reason = rule_fn(candidate)
        if flagged:
            return True, reason
    return False, ""


# ──────────────────────────────────────────────────────────────────────
# Individual detection rules
# ──────────────────────────────────────────────────────────────────────

def _rule_impossible_experience(c: Dict[str, Any]) -> Tuple[bool, str]:
    """Rule 1: years_experience > 45."""
    yrs = c.get("years_experience", 0) or 0
    if yrs > 45:
        return True, "impossible experience"
    return False, ""


def _rule_negative_experience(c: Dict[str, Any]) -> Tuple[bool, str]:
    """Rule 2: years_experience < 0."""
    yrs = c.get("years_experience", 0) or 0
    if yrs < 0:
        return True, "negative experience"
    return False, ""


def _rule_all_zero_signals(c: Dict[str, Any]) -> Tuple[bool, str]:
    """Rule 3: all numeric redrob_signals == 0."""
    signals = c.get("signals") or {}
    if not signals:
        return False, ""  # missing signals is not the same as all-zero
    numeric = _numeric_signal_values(signals)
    if numeric and all(v == 0 for v in numeric):
        return True, "all-zero signals (bot)"
    return False, ""


def _rule_perfect_signals(c: Dict[str, Any]) -> Tuple[bool, str]:
    """Rule 4: all numeric redrob_signals == 1.0."""
    signals = c.get("signals") or {}
    if not signals:
        return False, ""
    numeric = _numeric_signal_values(signals)
    if numeric and all(v == 1.0 for v in numeric):
        return True, "perfect signals (bot)"
    return False, ""


def _rule_skill_stuffing(c: Dict[str, Any]) -> Tuple[bool, str]:
    """Rule 5: more than 50 skills listed."""
    skills = c.get("skills_set") or set()
    # Also check raw skills list for count
    skills_raw = c.get("skills_raw") or []
    count = max(len(skills), len(skills_raw))
    if count > 50:
        return True, "skill stuffing"
    return False, ""


def _rule_future_graduation_with_experience(c: Dict[str, Any]) -> Tuple[bool, str]:
    """Rule 6: graduation_year > 2026 AND experience > 0."""
    edu = c.get("education") or {}
    grad_year = _safe_int(edu.get("graduation_year"))
    yrs = c.get("years_experience", 0) or 0
    if grad_year is not None and grad_year > 2026 and yrs > 0:
        return True, "future graduation"
    return False, ""


def _rule_invalid_signal_envelope(c: Dict[str, Any]) -> Tuple[bool, str]:
    """Rule 7: signal envelope invalid — rates > 1.0 or scores > 100."""
    signals = c.get("signals") or {}
    # Rates should be ≤ 1.0
    for key in ("recruiter_response_rate", "interview_completion_rate",
                "offer_acceptance_rate"):
        val = _safe_float(signals.get(key))
        if val is not None and val > 1.0:
            return True, "invalid envelope"
    # Scores should be ≤ 100
    for key in ("github_activity_score", "profile_completeness_score"):
        val = _safe_float(signals.get(key))
        if val is not None and val > 100.0:
            return True, "invalid envelope"
    return False, ""


def _rule_suspicious_name(c: Dict[str, Any]) -> Tuple[bool, str]:
    """Rule 8: repeated characters 4+ in name."""
    name = c.get("name") or ""
    if _has_repeated_chars(name, threshold=4):
        return True, "suspicious name/email"
    return False, ""


def _rule_impossible_job_duration(c: Dict[str, Any]) -> Tuple[bool, str]:
    """Rule 9: any job duration > 600 months (50 years)."""
    career = c.get("career_history") or []
    for job in career:
        if not isinstance(job, dict):
            continue
        dur = _safe_float(job.get("duration_months"))
        if dur is not None and dur > 600:
            return True, "impossible job duration"
    return False, ""


def _rule_expert_zero_months(c: Dict[str, Any]) -> Tuple[bool, str]:
    """Rule 10: 3+ skills with 'expert' proficiency but 0 months duration."""
    skills_raw: List[Dict[str, Any]] = c.get("skills_raw") or []
    count = 0
    for sk in skills_raw:
        if not isinstance(sk, dict):
            continue
        prof = (sk.get("proficiency") or "").lower()
        dur = _safe_float(sk.get("duration_months"))
        if prof == "expert" and dur is not None and dur == 0:
            count += 1
    if count >= 3:
        return True, "expert with 0 months"
    return False, ""


def _rule_future_education_end(c: Dict[str, Any]) -> Tuple[bool, str]:
    """Rule 11: education end_year > 2026."""
    edu = c.get("education") or {}
    end_year = _safe_int(edu.get("end_year") or edu.get("graduation_year"))
    # Only flag when combined with other suspicious patterns
    # (standalone future graduation is caught by rule 6 with experience check)
    if end_year is not None and end_year > 2026:
        yrs = c.get("years_experience", 0) or 0
        if yrs > 5:  # Clearly impossible
            return True, "future graduation year"
    return False, ""


def _rule_inconsistent_history(c: Dict[str, Any]) -> Tuple[bool, str]:
    """Rule 12: claimed years vs total career history delta > 15 years."""
    claimed_years = c.get("years_experience", 0) or 0
    career = c.get("career_history") or []
    if not career:
        return False, ""
    total_months = 0
    for job in career:
        if isinstance(job, dict):
            total_months += _safe_float(job.get("duration_months")) or 0
    history_years = total_months / 12.0
    delta = abs(claimed_years - history_years)
    if delta > 15:
        return True, "inconsistent history"
    return False, ""


# ──────────────────────────────────────────────────────────────────────
# Rule registry
# ──────────────────────────────────────────────────────────────────────

_RULES = [
    _rule_impossible_experience,
    _rule_negative_experience,
    _rule_all_zero_signals,
    _rule_perfect_signals,
    _rule_skill_stuffing,
    _rule_future_graduation_with_experience,
    _rule_invalid_signal_envelope,
    _rule_suspicious_name,
    _rule_impossible_job_duration,
    _rule_expert_zero_months,
    _rule_future_education_end,
    _rule_inconsistent_history,
]


# ──────────────────────────────────────────────────────────────────────
# Helpers
# ──────────────────────────────────────────────────────────────────────

def _numeric_signal_values(signals: Dict[str, Any]) -> List[float]:
    """Extract all numeric signal values, skipping dicts/strings/bools."""
    vals: List[float] = []
    for key, val in signals.items():
        if isinstance(val, (int, float)) and not isinstance(val, bool):
            vals.append(float(val))
    return vals


def _has_repeated_chars(text: str, threshold: int = 4) -> bool:
    """Check if text contains any character repeated threshold+ times."""
    if not text:
        return False
    return bool(re.search(r"(.)\1{" + str(threshold - 1) + r",}", text))


def _safe_float(val: Any) -> float | None:
    if val is None:
        return None
    try:
        return float(val)
    except (ValueError, TypeError):
        return None


def _safe_int(val: Any) -> int | None:
    if val is None:
        return None
    try:
        return int(val)
    except (ValueError, TypeError):
        return None

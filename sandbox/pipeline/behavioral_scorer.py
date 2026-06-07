"""
Behavioral / activity-signal scorer for the TalentMind AI ranking pipeline.

Computes a behavioural fitness score [0, 1] from the candidate's
redrob_signals — 10 weighted metrics plus boolean bonuses and an
inactivity penalty.

All computation is offline; no API calls or lookups.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple

# ──────────────────────────────────────────────────────────────────────
# Signal weights and normalisation constants
# ──────────────────────────────────────────────────────────────────────

_SIGNAL_WEIGHTS: List[Tuple[str, float, float]] = [
    # (signal_key,          weight,  normaliser)
    ("recruiter_response_rate",     0.20,  1.0),
    ("interview_completion_rate",   0.18,  1.0),
    ("github_activity_score",       0.15,  100.0),
    ("profile_completeness_score",  0.12,  100.0),
    ("skill_assessment_avg",        0.12,  100.0),   # virtual — computed below
    ("offer_acceptance_rate",       0.08,  1.0),
    ("endorsements_received",       0.05,  100.0),
    ("saved_by_recruiters_30d",     0.04,  20.0),
    ("connection_count",            0.03,  500.0),
    ("profile_views_received_30d",  0.03,  50.0),
]

# Reference date for inactivity calculation
_REFERENCE_DATE = datetime(2026, 6, 1)

# Maximum inactivity penalty
_MAX_INACTIVITY_PENALTY = 0.20


def compute_behavioral_score(
    signals: Dict[str, Any],
) -> Tuple[float, Dict[str, float]]:
    """
    Compute behavioral / activity fitness score from redrob_signals.

    Parameters
    ----------
    signals : dict
        Raw redrob_signals dict from the candidate record.

    Returns
    -------
    (score, breakdown) : (float, dict)
        score    — composite behavioral score clamped to [0.0, 1.0]
        breakdown — per-signal contribution dict for explainability
    """
    if not signals:
        return 0.0, {}

    breakdown: Dict[str, float] = {}
    total = 0.0

    for signal_key, weight, norm in _SIGNAL_WEIGHTS:
        if signal_key == "skill_assessment_avg":
            # Virtual signal: average of skill_assessment_scores
            raw_val = _compute_skill_assessment_avg(signals)
        else:
            raw_val = _safe_float(signals.get(signal_key), default=0.0)

        # Normalise to [0, 1]
        normalised = min(raw_val / norm, 1.0) if norm > 0 else 0.0
        contribution = weight * normalised
        breakdown[signal_key] = round(contribution, 4)
        total += contribution

    # ── Boolean bonuses ──────────────────────────────────────────────
    bonus = 0.0

    if signals.get("open_to_work_flag", False):
        bonus += 0.03
        breakdown["bonus_open_to_work"] = 0.03

    verified_contacts = 0
    if signals.get("verified_email", False):
        verified_contacts += 1
    if signals.get("verified_phone", False):
        verified_contacts += 1
    if verified_contacts > 0:
        v_bonus = 0.02
        bonus += v_bonus
        breakdown["bonus_verified_contacts"] = v_bonus

    if signals.get("linkedin_connected", False):
        bonus += 0.01
        breakdown["bonus_linkedin"] = 0.01

    total += bonus

    # ── Inactivity penalty ───────────────────────────────────────────
    inactivity_penalty = _compute_inactivity_penalty(signals)
    if inactivity_penalty > 0:
        total -= inactivity_penalty
        breakdown["penalty_inactivity"] = round(-inactivity_penalty, 4)

    # ── Clamp to [0, 1] ─────────────────────────────────────────────
    score = max(0.0, min(1.0, total))
    return score, breakdown


# ──────────────────────────────────────────────────────────────────────
# Helpers
# ──────────────────────────────────────────────────────────────────────

def _compute_skill_assessment_avg(signals: Dict[str, Any]) -> float:
    """Average of skill_assessment_scores dict values."""
    scores = signals.get("skill_assessment_scores")
    if not scores or not isinstance(scores, dict):
        return 0.0
    values = [
        _safe_float(v, 0.0)
        for v in scores.values()
        if v is not None
    ]
    return sum(values) / len(values) if values else 0.0


def _compute_inactivity_penalty(signals: Dict[str, Any]) -> float:
    """
    Compute inactivity penalty based on last_active_date.

    Up to -0.20 penalty for candidates inactive > 180 days.
    """
    last_active = signals.get("last_active_date")
    if not last_active:
        return 0.05  # Small penalty for missing activity data

    try:
        if isinstance(last_active, str):
            # Try multiple date formats
            for fmt in ("%Y-%m-%d", "%Y-%m-%dT%H:%M:%S", "%Y-%m-%dT%H:%M:%SZ"):
                try:
                    last_dt = datetime.strptime(last_active, fmt)
                    break
                except ValueError:
                    continue
            else:
                return 0.05  # Unparseable date
        elif isinstance(last_active, datetime):
            last_dt = last_active
        else:
            return 0.05
    except Exception:
        return 0.05

    days_inactive = (_REFERENCE_DATE - last_dt).days
    if days_inactive <= 0:
        return 0.0  # Active or future date — no penalty
    if days_inactive <= 30:
        return 0.0
    if days_inactive <= 90:
        return 0.05
    if days_inactive <= 180:
        return 0.10

    return _MAX_INACTIVITY_PENALTY


def _safe_float(val: Any, default: float = 0.0) -> float:
    """Safely convert to float."""
    if val is None:
        return default
    try:
        return float(val)
    except (ValueError, TypeError):
        return default

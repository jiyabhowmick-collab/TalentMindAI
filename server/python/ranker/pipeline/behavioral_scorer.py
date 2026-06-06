import datetime
import numpy as np

# ---------------------------------------------------------------------------
# Signal configuration: weight + normalization denominator.
# Weights sum to 1.00 across named signals.
# Boolean bonuses (open_to_work, verified contacts, linkedin) add up to +0.06
# on top, so the pre-clamp max is ~1.06 — always clamped to [0, 1].
# ---------------------------------------------------------------------------
SIGNAL_CONFIG: dict[str, dict] = {
    "recruiter_response_rate":    {"weight": 0.20, "norm": 1.0},
    "interview_completion_rate":  {"weight": 0.18, "norm": 1.0},
    "github_activity_score":      {"weight": 0.15, "norm": 100.0},   # -1 → treat as 0
    "profile_completeness_score": {"weight": 0.12, "norm": 100.0},
    "skill_assessment_avg":       {"weight": 0.12, "norm": 1.0},     # virtual key (pre-computed)
    "offer_acceptance_rate":      {"weight": 0.08, "norm": 1.0},     # -1 → treat as 0
    "endorsements_received":      {"weight": 0.05, "norm": 100.0},
    "saved_by_recruiters_30d":    {"weight": 0.04, "norm": 20.0},
    "connection_count":           {"weight": 0.03, "norm": 500.0},
    "profile_views_received_30d": {"weight": 0.03, "norm": 50.0},
}

# Reference date for inactivity penalty
_REFERENCE_DATE = datetime.date(2026, 6, 1)


def _skill_assessment_avg(signals: dict) -> float:
    """Average of skill_assessment_scores values normalised to [0, 1]."""
    sa = signals.get("skill_assessment_scores") or {}
    if isinstance(sa, dict) and sa:
        vals = [v for v in sa.values() if isinstance(v, (int, float)) and v >= 0]
        if vals:
            return min(sum(vals) / len(vals) / 100.0, 1.0)
    return 0.0


def _inactivity_penalty(signals: dict) -> float:
    """
    Up to 0.20 penalty for candidates who haven't been active recently.
    Reads 'last_active_date' as ISO date string (YYYY-MM-DD).
    Returns 0.0 if the field is missing or unparseable.
    """
    last_active = signals.get("last_active_date", "")
    if not last_active:
        return 0.0
    try:
        last_dt     = datetime.date.fromisoformat(str(last_active))
        days_inactive = (_REFERENCE_DATE - last_dt).days
        return float(max(0.0, min(0.20, days_inactive / 365 * 0.20)))
    except (ValueError, TypeError):
        return 0.0


def compute_behavioral_score(signals: dict) -> tuple[float, dict]:
    """
    Compute a behavioral score in [0, 1] from a redrob_signals dict.

    Typical range for average candidates: 0.35 – 0.65.
    High-quality active candidates: 0.65 – 0.85.

    Parameters
    ----------
    signals : dict
        Raw redrob_signals for a candidate.

    Returns
    -------
    (behavioral_score: float, breakdown: dict)
    """
    if not signals:
        return 0.0, {}

    # Build a working copy with the virtual skill_assessment_avg injected
    working = dict(signals)
    working["skill_assessment_avg"] = _skill_assessment_avg(signals)

    total     = 0.0
    breakdown: dict[str, float] = {}

    for key, cfg in SIGNAL_CONFIG.items():
        raw = working.get(key, 0)

        # None or missing → 0
        if raw is None:
            raw = 0.0

        # Sentinel -1 (no data) → treat as 0
        if isinstance(raw, (int, float)) and raw < 0:
            raw = 0.0

        try:
            normalised = float(raw) / cfg["norm"]
        except (TypeError, ValueError):
            normalised = 0.0

        normalised = min(normalised, 1.0)   # cap at 1.0
        weighted   = normalised * cfg["weight"]

        total           += weighted
        breakdown[key]   = round(normalised, 4)

    # ── Boolean bonuses (additive, capped by final clamp) ────────────────
    if signals.get("open_to_work_flag"):
        total += 0.03
        breakdown["open_to_work_flag"] = 1.0
    else:
        breakdown["open_to_work_flag"] = 0.0

    if signals.get("verified_email") and signals.get("verified_phone"):
        total += 0.02
        breakdown["verified_contacts"] = 1.0
    else:
        breakdown["verified_contacts"] = 0.0

    if signals.get("linkedin_connected"):
        total += 0.01
        breakdown["linkedin_connected"] = 1.0
    else:
        breakdown["linkedin_connected"] = 0.0

    # ── Inactivity penalty ────────────────────────────────────────────────
    penalty = _inactivity_penalty(signals)
    if penalty > 0:
        total                     -= penalty
        breakdown["inactivity_penalty"] = round(-penalty, 4)

    behavioral_score = round(float(np.clip(total, 0.0, 1.0)), 6)
    return behavioral_score, breakdown

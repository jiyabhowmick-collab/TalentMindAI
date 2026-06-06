import numpy as np

# ---------------------------------------------------------------------------
# Real redrob_signals weights — total = 1.00
# ---------------------------------------------------------------------------
SIGNAL_WEIGHTS: dict[str, float] = {
    "recruiter_response_rate":    0.18,  # already 0–1
    "interview_completion_rate":  0.15,  # already 0–1
    "profile_completeness_score": 0.12,  # divide by 100
    "github_activity_score":      0.10,  # divide by 100; -1 → 0
    "skill_assessment_avg":       0.10,  # virtual: avg(skill_assessment_scores) / 100
    "offer_acceptance_rate":      0.08,  # already 0–1; -1 → 0
    "endorsements_received":      0.07,  # divide by 100, cap 1.0
    "connection_count":           0.05,  # divide by 500, cap 1.0
    "saved_by_recruiters_30d":    0.05,  # divide by 20, cap 1.0
    "profile_views_received_30d": 0.04,  # divide by 50, cap 1.0
    "open_to_work_flag":          0.03,  # bool → 1.0 / 0.0
    "verified_email":             0.02,  # bool → 1.0 / 0.0
    "verified_phone":             0.01,  # bool → 1.0 / 0.0
}


def _to_float(value) -> float:
    """Cast a value to float; return 0.0 on failure."""
    if isinstance(value, bool):
        return 1.0 if value else 0.0
    try:
        return float(value)
    except (TypeError, ValueError):
        return 0.0


def _normalize(key: str, value) -> float:
    """
    Normalize a single signal to [0, 1] according to its field rules.
    """
    # Booleans first — before any numeric cast
    if isinstance(value, bool):
        return 1.0 if value else 0.0

    v = _to_float(value)

    # Sentinel -1 means "no data" for github and offer fields → treat as 0
    if v < 0:
        return 0.0

    if key == "profile_completeness_score":
        return float(np.clip(v / 100.0, 0.0, 1.0))

    if key == "github_activity_score":
        return float(np.clip(v / 100.0, 0.0, 1.0))

    if key == "endorsements_received":
        return float(np.clip(v / 100.0, 0.0, 1.0))

    if key == "connection_count":
        return float(np.clip(v / 500.0, 0.0, 1.0))

    if key == "saved_by_recruiters_30d":
        return float(np.clip(v / 20.0, 0.0, 1.0))

    if key == "profile_views_received_30d":
        return float(np.clip(v / 50.0, 0.0, 1.0))

    # Everything else (recruiter_response_rate, interview_completion_rate,
    # offer_acceptance_rate, skill_assessment_avg, open_to_work_flag,
    # verified_email, verified_phone) is already 0–1
    return float(np.clip(v, 0.0, 1.0))


def compute_behavioral_score(signals: dict) -> tuple[float, dict]:
    """
    Compute a behavioral score in [0, 1] from a redrob_signals dict.

    Parameters
    ----------
    signals : dict
        Raw redrob_signals for a candidate.

    Returns
    -------
    (behavioral_score: float, breakdown: dict)
        breakdown maps each signal key to its normalised [0, 1] value.
    """
    if not signals:
        return 0.0, {}

    # ── Build a working copy with the virtual skill_assessment_avg key ──────
    working = dict(signals)

    raw_scores = working.get("skill_assessment_scores", {})
    if isinstance(raw_scores, dict) and raw_scores:
        numeric = [v for v in raw_scores.values() if isinstance(v, (int, float))]
        skill_avg = (sum(numeric) / len(numeric) / 100.0) if numeric else 0.0
    else:
        skill_avg = 0.0
    working["skill_assessment_avg"] = skill_avg

    # ── Score every known signal ─────────────────────────────────────────────
    breakdown: dict[str, float] = {}
    weighted_sum = 0.0

    for key, weight in SIGNAL_WEIGHTS.items():
        raw_value = working.get(key, 0)
        if raw_value is None:
            raw_value = 0
        normalised = _normalize(key, raw_value)
        breakdown[key] = normalised
        weighted_sum += weight * normalised

    behavioral_score = float(np.clip(weighted_sum, 0.0, 1.0))
    return behavioral_score, breakdown

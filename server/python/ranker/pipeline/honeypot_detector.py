import re

CURRENT_YEAR = 2026


def is_honeypot(candidate: dict) -> tuple[bool, str]:
    """
    Returns (True, reason) if the candidate looks like a honeypot trap.
    Returns (False, "") otherwise.

    A candidate fails if ANY single condition is True.
    """

    # ── Field extraction ─────────────────────────────────────────────────
    # years_experience comes from the normalised dict; fall back to the
    # nested profile path for cases where the raw dict is passed directly.
    years_exp: float = (
        candidate.get("years_experience")
        or candidate.get("profile", {}).get("years_of_experience", 0)
        or 0
    )

    skills: list          = candidate.get("skills") or []
    redrob: dict          = candidate.get("redrob_signals") or {}
    education             = candidate.get("education")
    career: list          = candidate.get("career_history") or []
    name: str             = candidate.get("name") or ""
    email: str            = candidate.get("email") or ""

    # ── 1. Impossibly high experience ─────────────────────────────────────
    if years_exp > 45:
        return True, "impossible experience"

    # ── 2. Negative experience ────────────────────────────────────────────
    if years_exp < 0:
        return True, "negative experience"

    # ── 3. All redrob_signals values are exactly 0 ────────────────────────
    if redrob and all(v == 0 for v in redrob.values()):
        return True, "all-zero signals (bot)"

    # ── 4. All redrob_signals values are exactly 1.0 ─────────────────────
    if redrob and all(v == 1.0 for v in redrob.values()):
        return True, "perfect signals (bot)"

    # ── 5. Skill stuffing (raw skills list > 50) ──────────────────────────
    if len(skills) > 50:
        return True, "skill stuffing"

    # ── 6. Future graduation year with non-zero experience ────────────────
    graduation_year = None
    if isinstance(education, dict):
        graduation_year = education.get("graduation_year")
    elif isinstance(education, list):
        for item in education:
            if isinstance(item, dict) and "graduation_year" in item:
                graduation_year = item["graduation_year"]
                break

    if years_exp > 0 and graduation_year is not None:
        try:
            if int(graduation_year) > CURRENT_YEAR:
                return True, "future graduation"
        except (ValueError, TypeError):
            pass

    # ── 7. Explicit invalid signal envelope ───────────────────────────────
    if "signal_envelope_valid" in redrob and redrob["signal_envelope_valid"] is False:
        return True, "invalid envelope"

    # ── 8. Repeated characters (4+ in a row) in name or email ────────────
    _repeated = re.compile(r"(.)\1{3,}", re.IGNORECASE)
    if _repeated.search(name) or _repeated.search(email):
        return True, "suspicious name/email"

    # ── 9. Impossible job duration in career history ──────────────────────
    for job in career:
        if not isinstance(job, dict):
            continue
        duration = job.get("duration_months", 0) or 0
        try:
            duration = float(duration)
        except (TypeError, ValueError):
            duration = 0
        if duration > 600:   # > 50 years at a single role
            return True, "impossible job duration"

    # ── 10. Expert proficiency claimed on skills with 0 months used ───────
    if isinstance(skills, list):
        expert_zero = sum(
            1 for s in skills
            if isinstance(s, dict)
            and str(s.get("proficiency", "")).lower() == "expert"
            and s.get("duration_months") is not None
            and s.get("duration_months") == 0
        )
        if expert_zero >= 3:
            return True, f"expert proficiency with 0 months used on {expert_zero} skills"

    # ── 11. Future end_year in education entries ──────────────────────────
    if isinstance(education, list):
        for edu in education:
            if not isinstance(edu, dict):
                continue
            end_year = edu.get("end_year", 0)
            try:
                if int(end_year) > CURRENT_YEAR:
                    return True, f"future graduation year {int(end_year)}"
            except (TypeError, ValueError):
                pass

    # ── 12. Claimed experience wildly inconsistent with career history ─────
    if career:
        total_career_months: float = 0
        for job in career:
            if not isinstance(job, dict):
                continue
            try:
                total_career_months += float(job.get("duration_months", 0) or 0)
            except (TypeError, ValueError):
                pass

        # Use the nested profile path as the authoritative claimed value
        claimed_years: float = (
            candidate.get("years_experience")
            or candidate.get("profile", {}).get("years_of_experience", 0)
            or 0
        )
        career_years = total_career_months / 12

        if claimed_years > 0 and abs(claimed_years - career_years) > 15:
            return True, (
                f"claimed {claimed_years}yrs but career history shows "
                f"{career_years:.1f}yrs"
            )

    return False, ""

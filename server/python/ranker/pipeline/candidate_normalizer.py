from utils.text_utils import extract_skills_from_text, compute_seniority_level
from pipeline.honeypot_detector import is_honeypot

# ---------------------------------------------------------------------------
# Education keyword maps — checked in descending priority order
# ---------------------------------------------------------------------------
_EDU_LEVEL_KEYWORDS: list[tuple[int, tuple[str, ...]]] = [
    (4, ("phd", "doctorate", "ph.d")),
    (3, ("master", "msc", "mba", "m.s", "m.tech")),
    (2, ("bachelor", "bsc", "b.tech", "b.e", "b.s", "undergraduate")),
    (1, ("diploma", "associate")),
]


def _parse_education_level(education) -> int:
    """
    Derive an integer education level from the raw education field.
    Accepts a list of dicts, a single dict, a plain string, or None.
    Returns 0 (none/unknown) if no recognised keyword is found.
    """
    if not education:
        return 0

    texts: list[str] = []

    if isinstance(education, str):
        texts.append(education.lower())
    elif isinstance(education, dict):
        texts.extend(str(v).lower() for v in education.values() if v)
    elif isinstance(education, list):
        for item in education:
            if isinstance(item, str):
                texts.append(item.lower())
            elif isinstance(item, dict):
                texts.extend(str(v).lower() for v in item.values() if v)

    combined = " ".join(texts)

    for level, keywords in _EDU_LEVEL_KEYWORDS:
        if any(kw in combined for kw in keywords):
            return level

    return 0


def normalize_candidate(raw: dict) -> dict:
    """
    Takes a raw candidate dict from JSONL and returns a normalized profile.

    Actual schema has profile fields nested under raw["profile"], skills as
    raw["skills"] (list of {"name": ...} objects), and behavioral signals
    under raw["redrob_signals"].

    Returns
    -------
    {
        "candidate_id":     str,
        "name":             str,                # anonymized_name
        "current_title":    str,                # lowercased
        "years_experience": float,              # clamped to [0, 50]
        "skills_set":       set[str],           # from skills list + text mining
        "seniority_level":  int,                # 1-4
        "education_level":  int,                # 0-4
        "signals":          dict,               # raw redrob_signals, default {}
        "is_honeypot":      bool,
        "honeypot_reason":  str,
        "_raw":             dict,               # original dict preserved
    }
    """
    # ── Sub-objects ──────────────────────────────────────────────────────────
    profile: dict  = raw.get("profile") or {}
    signals: dict  = raw.get("redrob_signals") or {}
    if not isinstance(signals, dict):
        signals = {}

    # ── Scalar fields ────────────────────────────────────────────────────────
    candidate_id  = str(raw.get("candidate_id") or "")
    name          = str(profile.get("anonymized_name") or "")
    current_title = str(profile.get("current_title") or "").lower()

    # ── Years of experience ──────────────────────────────────────────────────
    try:
        years_raw = float(profile.get("years_of_experience") or 0)
    except (ValueError, TypeError):
        years_raw = 0.0
    years_experience = max(0.0, min(50.0, years_raw))

    # ── Skills ───────────────────────────────────────────────────────────────
    # Each item in raw["skills"] is {"name": "Python", ...}
    raw_skills = raw.get("skills") or []
    if isinstance(raw_skills, list):
        explicit_skills: set[str] = {
            str(s["name"]).lower().strip()
            for s in raw_skills
            if isinstance(s, dict) and s.get("name")
        }
    else:
        explicit_skills = set()

    # Mine skills from free-text profile fields
    summary  = str(profile.get("summary")  or "")
    headline = str(profile.get("headline") or "")
    mined_skills: set[str] = set()
    if summary:
        mined_skills |= extract_skills_from_text(summary)
    if headline:
        mined_skills |= extract_skills_from_text(headline)

    skills_set = explicit_skills | mined_skills

    # ── Title-implied skills ──────────────────────────────────────────────────
    # Prevent ML Engineers / Data Scientists being penalised for not listing
    # compound skills that are self-evident from their job title.
    title_text = current_title  # already lowercased
    if "machine learning" in title_text or " ml " in title_text or title_text.startswith("ml "):
        skills_set.add("machine learning")
    if "deep learning" in title_text:
        skills_set.add("deep learning")
    if "nlp" in title_text or "natural language" in title_text:
        skills_set.add("nlp")
    if "data sci" in title_text:
        skills_set.update({"data science", "python"})
    if "data engineer" in title_text:
        skills_set.update({"data engineering", "sql"})
    if "devops" in title_text:
        skills_set.add("devops")
    if "computer vision" in title_text:
        skills_set.add("computer vision")

    # Also mine compound skills from each career history title
    for job in raw.get("career_history") or []:
        if not isinstance(job, dict):
            continue
        job_title = str(job.get("title") or "").lower()
        if "machine learning" in job_title or " ml " in job_title:
            skills_set.add("machine learning")
        if "deep learning" in job_title:
            skills_set.add("deep learning")
        if "nlp" in job_title or "natural language" in job_title:
            skills_set.add("nlp")
        if "data sci" in job_title:
            skills_set.update({"data science", "python"})
        if "data engineer" in job_title:
            skills_set.update({"data engineering", "sql"})

    # ── Seniority ────────────────────────────────────────────────────────────
    seniority_level = compute_seniority_level(years_experience, current_title)

    # ── Education ────────────────────────────────────────────────────────────
    education_level = _parse_education_level(raw.get("education"))

    # ── Honeypot check ───────────────────────────────────────────────────────
    honeypot_input = {
        "years_experience": years_experience,
        "skills":           raw.get("skills") or [],   # raw dicts — needed for proficiency/duration checks
        "redrob_signals":   signals,
        "education":        raw.get("education"),
        "career_history":   raw.get("career_history") or [],
        "profile":          profile,                   # for career consistency check
        "name":             name,
        "email":            str(raw.get("email") or ""),
    }
    flagged, reason = is_honeypot(honeypot_input)

    return {
        "candidate_id":     candidate_id,
        "name":             name,
        "current_title":    current_title,
        "years_experience": years_experience,
        "skills_set":       skills_set,
        "seniority_level":  seniority_level,
        "education_level":  education_level,
        "signals":          signals,
        "is_honeypot":      flagged,
        "honeypot_reason":  reason,
        "_raw":             raw,
    }

"""
Pre-filter: O(n) single-pass triage on *raw* candidates BEFORE normalisation.

Runs on raw JSONL dicts (not normalised), so it must be tolerant of missing
keys.  The goal is to eliminate ~85 % of candidates cheaply so that the
expensive normalisation + scoring stages only process ~15 k out of 100 k.

JD-ADAPTIVE: Extracts title keywords and skill keywords from the JD itself,
so filtering adapts to any role — not just ML.

Three buckets
─────────────
  definite  – title overlaps with JD title keywords       → always normalise & score
  possible  – has JD-relevant skills but not title match   → normalise & score as backup
  disqualified – neither relevant title nor relevant skills → skip entirely
"""

import logging
import re

logger = logging.getLogger(__name__)

# ── Stopwords to ignore when tokenizing titles ───────────────────────────────
_TITLE_STOPWORDS: frozenset[str] = frozenset({
    "a", "an", "the", "and", "or", "of", "in", "at", "to", "for", "with",
    "is", "are", "was", "-", "/", "&", "|", ",", ".", "(", ")", "–",
    "i", "ii", "iii", "iv", "v",  # roman numerals for levels
})


def _tokenize_title(title: str) -> set[str]:
    """Split a title into meaningful lowercase word tokens."""
    # Normalize separators
    title = re.sub(r'[/|&,\-–]+', ' ', title.lower())
    words = title.split()
    return {w.strip() for w in words if len(w) > 1 and w not in _TITLE_STOPWORDS}


def _extract_jd_title_keywords(jd_profile: dict) -> set[str]:
    """
    Extract title-relevant keywords from the JD.
    Uses the raw JD text first line (usually the job title) + tokens.
    """
    keywords: set[str] = set()

    # 1. First line of raw text is typically the job title
    raw_text = jd_profile.get("raw_text", "")
    if raw_text:
        first_line = raw_text.strip().split("\n")[0].strip()
        keywords |= _tokenize_title(first_line)

    # 2. Add JD tokens (from jd_parser's tokenize — already lowered, stopwords removed)
    tokens = jd_profile.get("tokens") or []
    # Take the top tokens that appear in the first few lines (more title-relevant)
    keywords |= set(tokens[:15])

    # 3. Also add domain keywords from jd_parser
    domain_kw = jd_profile.get("domain_keywords") or []
    keywords |= set(domain_kw[:10])

    # Remove very generic words that don't help filtering
    keywords -= {"experience", "years", "work", "working", "team", "role",
                 "looking", "company", "join", "position", "requirements",
                 "required", "skills", "candidate", "ideal", "strong",
                 "must", "have", "including", "etc", "ability", "using",
                 "knowledge", "good", "need", "based", "new", "please"}

    return keywords


def _extract_jd_skill_keywords(jd_profile: dict) -> set[str]:
    """
    Extract skill keywords from the JD for cheap pre-filter matching.
    Uses required_skills + preferred_skills from jd_parser.
    """
    skills: set[str] = set()

    required = jd_profile.get("required_skills")
    if required:
        if isinstance(required, set):
            skills |= required
        else:
            skills |= set(required)

    preferred = jd_profile.get("preferred_skills")
    if preferred:
        if isinstance(preferred, set):
            skills |= preferred
        else:
            skills |= set(preferred)

    # Also extract individual words from multi-word skills for broader matching
    skill_words: set[str] = set()
    for skill in skills:
        for word in skill.lower().split():
            if len(word) > 2:
                skill_words.add(word)

    return skills | skill_words


def _extract_raw_title(raw: dict) -> str:
    """Get lowered title from a raw JSONL dict (before normalisation)."""
    profile = raw.get("profile") or {}
    title = profile.get("current_title") or ""
    return str(title).lower().strip()


def _extract_raw_skill_names(raw: dict) -> set[str]:
    """
    Get a set of lowered skill names from the raw skills list.
    Each item is expected to be {"name": "Python", ...}.
    Only reads the first 20 skills for speed.
    """
    raw_skills = raw.get("skills") or []
    if not isinstance(raw_skills, list):
        return set()
    result: set[str] = set()
    for s in raw_skills[:20]:  # only check first 20 for speed
        if isinstance(s, dict):
            name = s.get("name")
            if name:
                result.add(str(name).lower().strip())
    return result


def prefilter_candidates(
    raw_candidates: list[dict],
    jd_profile: dict | None = None,
) -> tuple[list[dict], list[dict], int]:
    """
    JD-adaptive single-pass O(n) triage.

    Parameters
    ----------
    raw_candidates : list[dict]
        Raw JSONL dicts (not normalised).
    jd_profile : dict, optional
        Parsed JD profile — used to extract title keywords and skill keywords.

    Returns
    -------
    (definite, possible, disqualified_count)
        definite  : raw dicts whose title overlaps with JD title keywords.
        possible  : raw dicts that have JD-relevant skills but not a matching title.
        disqualified_count : int, how many were discarded.
    """
    # Extract JD-specific keywords for adaptive filtering
    if jd_profile:
        jd_title_keywords = _extract_jd_title_keywords(jd_profile)
        jd_skill_keywords = _extract_jd_skill_keywords(jd_profile)
    else:
        # Fallback — pass everything through
        return raw_candidates, [], 0

    logger.debug(
        "Pre-filter JD keywords: title=%s  skills=%s",
        sorted(jd_title_keywords)[:15],
        sorted(jd_skill_keywords)[:15],
    )

    # If we couldn't extract any meaningful keywords, pass everything through
    if not jd_title_keywords and not jd_skill_keywords:
        logger.warning("Pre-filter: no JD keywords extracted — passing all candidates through")
        return raw_candidates, [], 0

    definite: list[dict] = []
    possible: list[dict] = []
    disqualified_count = 0

    for raw in raw_candidates:
        title = _extract_raw_title(raw)
        title_words = _tokenize_title(title)

        # Title overlaps with JD title keywords → definite
        if jd_title_keywords and title_words & jd_title_keywords:
            definite.append(raw)
            continue

        # No title match — check if they have JD-relevant skills
        if jd_skill_keywords:
            skill_names = _extract_raw_skill_names(raw)
            if skill_names & jd_skill_keywords:
                possible.append(raw)
                continue

        disqualified_count += 1

    logger.info(
        "Pre-filter: %d definite, %d possible, %d disqualified (%.1f%% eliminated) "
        "| JD title keywords: %s",
        len(definite), len(possible), disqualified_count,
        disqualified_count / max(len(raw_candidates), 1) * 100,
        sorted(jd_title_keywords)[:8],
    )

    # Safety: if we filtered out too aggressively (>95%), include possibles as definite
    survivor_count = len(definite) + len(possible)
    if survivor_count < max(100, len(raw_candidates) * 0.05):
        logger.warning(
            "Pre-filter too aggressive (%d survivors from %d) — falling back to full pipeline",
            survivor_count, len(raw_candidates),
        )
        return raw_candidates, [], 0

    return definite, possible, disqualified_count

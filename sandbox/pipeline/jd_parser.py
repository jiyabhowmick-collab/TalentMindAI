"""
Job Description parser for the TalentMind AI ranking pipeline.

Parses free-form JD text into a structured profile dict containing:
    required_skills, preferred_skills, must_have_flags, min_years,
    seniority_level, domain_keywords, and full token list.

All extraction is regex/set-based — no LLM or external API calls.
"""

from __future__ import annotations

import re
from collections import Counter
from typing import Any, Dict, List, Set

from sandbox.utils.text_utils import (
    TECH_SKILLS,
    compute_seniority_level,
    extract_skills_from_text,
    extract_years_from_text,
    tokenize,
)


def parse_job_description(jd_text: str) -> Dict[str, Any]:
    """
    Parse a job description string into a structured profile dict.

    Parameters
    ----------
    jd_text : str
        Raw job description text.

    Returns
    -------
    dict with keys:
        raw_text            – original text
        tokens              – tokenized word list
        required_skills     – set[str] of required skills
        preferred_skills    – set[str] of preferred/nice-to-have skills
        must_have_flags     – list[str] of must-have phrases
        min_years           – float | None
        seniority_level     – int 1-4
        domain_keywords     – list[str] top-20 non-skill tokens by frequency
        title_keywords      – set[str] extracted from first line / title
    """
    if not jd_text or not jd_text.strip():
        return _empty_profile()

    raw = jd_text.strip()
    tokens = tokenize(raw)

    # ── Extract title from first non-empty line ──────────────────────
    lines = [ln.strip() for ln in raw.splitlines() if ln.strip()]
    title_line = lines[0] if lines else ""
    title_keywords = set(tokenize(title_line))

    # ── Section-aware skill extraction ───────────────────────────────
    required_skills: Set[str] = set()
    preferred_skills: Set[str] = set()
    must_have_flags: List[str] = []

    # Split into rough sections
    sections = _split_sections(raw)

    for label, body in sections.items():
        skills = extract_skills_from_text(body)
        label_lower = label.lower()
        if any(kw in label_lower for kw in
               ("require", "must", "essential", "mandatory", "need")):
            required_skills |= skills
        elif any(kw in label_lower for kw in
                 ("prefer", "nice", "bonus", "plus", "desire", "optional")):
            preferred_skills |= skills
        else:
            # Default: add to required
            required_skills |= skills

    # If no section parsing worked, extract all skills as required
    if not required_skills:
        required_skills = extract_skills_from_text(raw)

    # Must-have flags: extract "must have ..." phrases
    for m in re.finditer(r"must\s+have[:\s]+([^\n.]+)", raw, re.IGNORECASE):
        must_have_flags.append(m.group(1).strip())

    # ── Years & Seniority ────────────────────────────────────────────
    min_years = extract_years_from_text(raw)
    seniority_level = compute_seniority_level(min_years, title_line)

    # ── Domain keywords (non-skill tokens by frequency) ──────────────
    skill_tokens = set()
    for s in required_skills | preferred_skills:
        skill_tokens |= set(s.lower().split())

    token_freq = Counter(tokens)
    domain_keywords = [
        tok for tok, _ in token_freq.most_common(40)
        if tok not in skill_tokens and tok not in TECH_SKILLS and len(tok) > 2
    ][:20]

    return {
        "raw_text": raw,
        "tokens": tokens,
        "required_skills": required_skills,
        "preferred_skills": preferred_skills,
        "must_have_flags": must_have_flags,
        "min_years": min_years,
        "seniority_level": seniority_level,
        "domain_keywords": domain_keywords,
        "title_keywords": title_keywords,
    }


# ──────────────────────────────────────────────────────────────────────
# Helpers
# ──────────────────────────────────────────────────────────────────────

def _split_sections(text: str) -> Dict[str, str]:
    """
    Split JD text into labelled sections based on common headings.

    Returns a dict mapping section label → body text.
    Unrecognised content goes under "_general".
    """
    section_re = re.compile(
        r"^[ \t]*(required|must have|nice to have|preferred|responsibilities|"
        r"qualifications|requirements|what you|about the|bonus|essential|"
        r"desirable|skills|experience|education)[^:\n]*[:\-]?\s*$",
        re.IGNORECASE | re.MULTILINE,
    )
    parts: Dict[str, str] = {}
    last_label = "_general"
    last_pos = 0

    for m in section_re.finditer(text):
        # Save preceding text under previous label
        parts.setdefault(last_label, "")
        parts[last_label] += text[last_pos:m.start()] + "\n"
        last_label = m.group(1).strip().lower()
        last_pos = m.end()

    # Remaining text
    parts.setdefault(last_label, "")
    parts[last_label] += text[last_pos:]

    return parts


def _empty_profile() -> Dict[str, Any]:
    """Return an empty JD profile with all expected keys."""
    return {
        "raw_text": "",
        "tokens": [],
        "required_skills": set(),
        "preferred_skills": set(),
        "must_have_flags": [],
        "min_years": None,
        "seniority_level": 2,
        "domain_keywords": [],
        "title_keywords": set(),
    }

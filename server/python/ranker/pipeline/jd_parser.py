import re
import logging
from collections import Counter

from utils.text_utils import (
    tokenize,
    extract_years_from_text,
    extract_skills_from_text,
    compute_seniority_level,
)

logger = logging.getLogger(__name__)

# Keywords that signal a preferred/optional requirement sentence
_PREFERRED_SIGNALS = ("preferred", "nice to have", "bonus", "plus", "desirable")

# Keywords that signal a hard requirement sentence
_MUST_HAVE_SIGNALS = ("required", "must have", "mandatory", "essential", "need")


def _split_sentences(text: str) -> list[str]:
    """
    Split text into sentences/lines.
    First splits on newlines, then on sentence-ending punctuation so that
    both bullet-point JDs and prose JDs are handled correctly.
    """
    # Split on newlines first
    lines = re.split(r"\n+", text)
    sentences: list[str] = []
    for line in lines:
        # Further split on '. ', '! ', '? ' to handle prose paragraphs
        parts = re.split(r"(?<=[.!?])\s+", line.strip())
        sentences.extend(p for p in parts if p)
    return sentences


def _sentences_matching(sentences: list[str], signals: tuple[str, ...]) -> list[str]:
    """Return sentences that contain at least one of the given signal phrases."""
    matched: list[str] = []
    for sentence in sentences:
        lower = sentence.lower()
        if any(signal in lower for signal in signals):
            matched.append(sentence)
    return matched


def parse_job_description(jd_text: str) -> dict:
    """
    Returns a structured JD profile::

        {
            "raw_text":        str,
            "tokens":          list[str],   # all tokens from the full text
            "required_skills": set[str],    # skills extracted from the full text
            "preferred_skills": set[str],   # skills near preferred/bonus signals
            "min_years":       float,       # minimum years required, default 0
            "seniority_level": int,         # 1-4
            "domain_keywords": list[str],   # top-20 tokens by freq, skills removed
            "must_have_flags": list[str],   # skills near required/must signals
        }
    """
    sentences = _split_sentences(jd_text)

    # ------------------------------------------------------------------ tokens
    tokens = tokenize(jd_text)

    # --------------------------------------------------------- required_skills
    required_skills = extract_skills_from_text(jd_text)

    # -------------------------------------------------------- preferred_skills
    preferred_sentences = _sentences_matching(sentences, _PREFERRED_SIGNALS)
    preferred_skills: set[str] = set()
    for sent in preferred_sentences:
        preferred_skills |= extract_skills_from_text(sent)

    # ---------------------------------------------------------- must_have_flags
    must_sentences = _sentences_matching(sentences, _MUST_HAVE_SIGNALS)
    must_have_flags: list[str] = []
    seen_must: set[str] = set()
    for sent in must_sentences:
        for skill in extract_skills_from_text(sent):
            if skill not in seen_must:
                seen_must.add(skill)
                must_have_flags.append(skill)

    # ------------------------------------------------------------- min_years
    min_years = extract_years_from_text(jd_text) or 0.0

    # -------------------------------------------------------- seniority_level
    # Use the first line / title heuristic: take the first non-empty line as
    # a proxy for the job title; fall back to empty string if absent.
    first_line = next((s for s in sentences if s.strip()), "")
    seniority_level = compute_seniority_level(min_years, first_line)

    # -------------------------------------------------------- domain_keywords
    # Flatten all skills into a set of individual words so we can exclude them
    skill_words: set[str] = set()
    for skill in required_skills:
        skill_words.update(skill.split())

    non_skill_tokens = [t for t in tokens if t not in skill_words]
    token_counts = Counter(non_skill_tokens)
    domain_keywords = [word for word, _ in token_counts.most_common(20)]

    # ── Debug: log JD extraction results ─────────────────────────────────
    logger.debug("DEBUG JD required_skills: %s", sorted(required_skills))
    logger.debug("DEBUG JD must_have_flags: %s", must_have_flags)
    logger.debug("DEBUG JD tokens sample:   %s", tokens[:20])
    logger.debug("DEBUG JD min_years=%.1f  seniority=%d", min_years, seniority_level)

    return {
        "raw_text": jd_text,
        "tokens": tokens,
        "required_skills": required_skills,
        "preferred_skills": preferred_skills,
        "min_years": min_years,
        "seniority_level": seniority_level,
        "domain_keywords": domain_keywords,
        "must_have_flags": must_have_flags,
    }

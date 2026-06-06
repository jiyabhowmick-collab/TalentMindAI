from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np
import logging

logger = logging.getLogger(__name__)

# Fired once per Flask request to avoid log flooding
_debug_logged = False

# Free-text fields to mine from a candidate dict when building the corpus
_CANDIDATE_TEXT_FIELDS = ("summary", "bio", "description", "about", "overview", "profile")


def _candidate_to_text(candidate: dict) -> str:
    """
    Build a single string representation of a candidate for TF-IDF.
    Concatenates: current_title + skills_set + any free-text fields.
    """
    parts: list[str] = []

    title = candidate.get("current_title") or ""
    if title:
        parts.append(title)

    skills = candidate.get("skills_set") or set()
    if skills:
        parts.append(" ".join(sorted(skills)))

    for field in _CANDIDATE_TEXT_FIELDS:
        value = candidate.get("_raw", {}).get(field) if "_raw" in candidate else candidate.get(field)
        if value and isinstance(value, str):
            parts.append(value)

    return " ".join(parts)


def build_tfidf_scorer(jd_profile: dict, all_candidates: list[dict]):
    """
    Pre-computes a TF-IDF matrix for the entire candidate pool.
    """
    global _debug_logged
    _debug_logged = False   # reset per request so first candidate always logs
    jd_text = jd_profile.get("raw_text") or " ".join(jd_profile.get("tokens", []))

    candidate_texts = [_candidate_to_text(c) for c in all_candidates]

    corpus = [jd_text] + candidate_texts

    vectorizer = TfidfVectorizer(
        ngram_range=(1, 2),
        max_features=5000,
        sublinear_tf=True,
    )
    tfidf_matrix = vectorizer.fit_transform(corpus)

    jd_vector = tfidf_matrix[0]           # shape (1, n_features)
    candidate_vectors = tfidf_matrix[1:]   # shape (n_candidates, n_features)

    # cosine_similarity returns shape (1, n_candidates); flatten to 1-D
    similarities: np.ndarray = cosine_similarity(jd_vector, candidate_vectors).flatten()

    return similarities


def compute_semantic_score(candidate: dict, jd_profile: dict, tfidf_score: float) -> float:
    """
    Combines multiple signals into a final semantic score in [0, 1].

    Component weights
    -----------------
    a) TF-IDF cosine similarity     0.30
    b) Skill overlap F1             0.30
    c) Title relevance              0.25  ← replaces old must-have-only component
    d) Must-have coverage           0.10
    e) Seniority match              0.05

    Parameters
    ----------
    candidate   : normalised candidate dict (output of normalize_candidate)
    jd_profile  : parsed JD dict (output of parse_job_description)
    tfidf_score : pre-computed cosine similarity from build_tfidf_scorer

    Returns
    -------
    float in [0.0, 1.0]
    """
    # ── a) TF-IDF similarity ─────────────────────────────────────────────
    tfidf_component = float(np.clip(tfidf_score, 0.0, 1.0)) * 0.30

    # ── b) Skill overlap F1 ──────────────────────────────────────────────
    cand_skills: set[str] = candidate.get("skills_set") or set()
    jd_required: set[str] = jd_profile.get("required_skills") or set()

    if cand_skills and jd_required:
        overlap   = len(cand_skills & jd_required)
        precision = overlap / len(cand_skills)
        recall    = overlap / len(jd_required)
        f1 = (2 * precision * recall / (precision + recall)) if (precision + recall) > 0 else 0.0
    else:
        overlap = 0
        f1 = 0.0
    skill_component = f1 * 0.30

    # ── c) Title relevance ───────────────────────────────────────────────
    title     = candidate.get("current_title", "").lower()
    jd_tokens = set(jd_profile.get("tokens") or [])
    jd_raw    = (jd_profile.get("raw_text") or "").lower()

    # Token-level overlap between title words and JD vocabulary
    title_tokens  = set(title.replace("-", " ").split())
    title_overlap = len(title_tokens & jd_tokens)
    title_score   = min(title_overlap / max(len(title_tokens), 1), 1.0)

    # Exact role-match bonuses — floor the score so strong matches always rank well
    if ("machine learning engineer" in title or "ml engineer" in title):
        if ("machine learning engineer" in jd_raw or "ml engineer" in jd_raw
                or "machine learning" in jd_raw):
            title_score = max(title_score, 0.85)
    elif "data scientist" in title and "data scientist" in jd_raw:
        title_score = max(title_score, 0.70)
    elif "ai engineer" in title and ("ai engineer" in jd_raw or "machine learning" in jd_raw):
        title_score = max(title_score, 0.65)
    elif "data engineer" in title and "data engineer" in jd_raw:
        title_score = max(title_score, 0.65)
    elif "software engineer" in title and "software engineer" in jd_raw:
        title_score = max(title_score, 0.60)

    title_component = title_score * 0.25

    # ── d) Must-have coverage ────────────────────────────────────────────
    must_haves: set[str] = set(jd_profile.get("must_have_flags") or [])
    if must_haves:
        covered = len(cand_skills & must_haves) / len(must_haves)
    else:
        covered = 0.5   # neutral when JD has no explicit must-haves
    must_component = covered * 0.10

    # ── e) Seniority match ───────────────────────────────────────────────
    diff             = abs((candidate.get("seniority_level") or 2) - (jd_profile.get("seniority_level") or 2))
    seniority_score  = max(0.0, 1.0 - diff * 0.3)
    seniority_component = seniority_score * 0.05

    # ── Weighted sum ─────────────────────────────────────────────────────
    total = tfidf_component + skill_component + title_component + must_component + seniority_component

    # ── Debug: log breakdown for the first candidate scored per request ──
    global _debug_logged
    if not _debug_logged:
        _debug_logged = True
        logger.debug(
            "SEMANTIC BREAKDOWN  "
            "tfidf=%.3f×0.30=%.3f  "
            "skill_f1=%.3f×0.30=%.3f  "
            "title=%.3f×0.25=%.3f  "
            "must=%.3f×0.10=%.3f  "
            "seniority=%.3f×0.05=%.3f  "
            "→ total=%.4f  "
            "| skills=%d  jd_req=%d  overlap=%d  title=%r",
            float(np.clip(tfidf_score, 0.0, 1.0)), tfidf_component,
            f1, skill_component,
            title_score, title_component,
            covered, must_component,
            seniority_score, seniority_component,
            total,
            len(cand_skills), len(jd_required), overlap, title,
        )

    return float(np.clip(total, 0.0, 1.0))

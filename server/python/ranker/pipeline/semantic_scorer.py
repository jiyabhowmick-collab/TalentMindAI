"""
Semantic scorer — JD-adaptive title similarity + skill F1 + experience fit.

Replaces the previous TF-IDF + cosine-similarity approach which was the #1
bottleneck (~45s on 100k candidates).  The new scorer runs in O(1) per
candidate using word-overlap title scoring and set-intersection skill F1.

ALL scoring is JD-ADAPTIVE — works for any role (ML, Frontend, Data Engineer,
DevOps, etc.) by comparing candidate attributes against the actual JD content.

Component weights (sum to 1.0)
──────────────────────────────
  A) Title relevance      0.40   — word-overlap with JD title + seniority bonus
  B) Skill relevance F1   0.30   — set intersection with synonym expansion
  C) TF-IDF (legacy)      0.15   — kept for backward compat, receives actual value
  D) Experience fit       0.10   — years vs JD requirement
  E) Seniority match      0.05   — level delta penalty
"""

import re
import logging
import numpy as np

logger = logging.getLogger(__name__)

# Fired once per Flask request to avoid log flooding
_debug_logged = False

# ── Stopwords to ignore when computing title overlap ─────────────────────────
_TITLE_STOPWORDS: frozenset[str] = frozenset({
    "a", "an", "the", "and", "or", "of", "in", "at", "to", "for", "with",
    "is", "are", "was", "-", "/", "&", "|", ",", ".", "(", ")",
})

# ── Seniority keywords and their bonus values ────────────────────────────────
_SENIORITY_KEYWORDS: dict[str, float] = {
    "chief": 0.08, "vp": 0.08, "director": 0.07,
    "principal": 0.06, "staff": 0.06,
    "lead": 0.05, "head": 0.05,
    "senior": 0.04, "sr": 0.04, "sr.": 0.04,
    "junior": -0.02, "jr": -0.02, "jr.": -0.02,
    "intern": -0.05, "trainee": -0.05,
    "associate": -0.01, "entry": -0.03,
}


def _tokenize_title(title: str) -> set[str]:
    """Split a title into meaningful lowercase word tokens."""
    title = re.sub(r'[/|&,\-–()]+', ' ', title.lower())
    words = title.split()
    return {w.strip() for w in words if len(w) > 1 and w not in _TITLE_STOPWORDS}


def _get_jd_title_words(jd_profile: dict) -> set[str]:
    """
    Extract the target job title words from the JD.
    Uses first line of raw text (usually the job title) + domain keywords.
    Cached on the jd_profile dict to avoid recomputation.
    """
    # Check cache
    if "_jd_title_words" in jd_profile:
        return jd_profile["_jd_title_words"]

    words: set[str] = set()

    # 1. First line of raw text is typically the job title
    raw_text = jd_profile.get("raw_text", "")
    if raw_text:
        first_line = raw_text.strip().split("\n")[0].strip()
        words |= _tokenize_title(first_line)

    # 2. Domain keywords from jd_parser
    domain_kw = jd_profile.get("domain_keywords") or []
    words |= set(domain_kw[:10])

    # Remove very generic words that don't help scoring
    words -= {"experience", "years", "work", "working", "team", "role",
              "looking", "company", "join", "position", "requirements",
              "required", "skills", "candidate", "ideal", "strong",
              "must", "have", "including", "etc", "ability", "using",
              "knowledge", "good", "need", "based", "new", "please",
              "minimum", "responsibilities", "qualifications", "about"}

    # Remove seniority words from the base set — they're scored separately
    words -= set(_SENIORITY_KEYWORDS.keys())

    jd_profile["_jd_title_words"] = words
    return words


def compute_title_score(candidate_title: str, jd_profile: dict) -> float:
    """
    JD-adaptive title relevance score.

    Computes word overlap between the candidate's title and the JD title,
    then applies seniority bonuses/penalties.

    Returns a score in [0, 1].
    """
    jd_title_words = _get_jd_title_words(jd_profile)
    if not jd_title_words:
        return 0.30  # neutral if we can't extract JD title

    cand_words = _tokenize_title(candidate_title)
    if not cand_words:
        return 0.05

    # Remove seniority words from both for base comparison
    seniority_keys = set(_SENIORITY_KEYWORDS.keys())
    cand_content = cand_words - seniority_keys
    jd_content = jd_title_words - seniority_keys

    if not jd_content:
        return 0.30  # neutral

    # Base score: Jaccard-like overlap between content words
    overlap = cand_content & jd_content
    union = cand_content | jd_content

    if not union:
        return 0.10

    # Weighted overlap — recall matters more than precision
    recall = len(overlap) / len(jd_content) if jd_content else 0
    precision = len(overlap) / len(cand_content) if cand_content else 0
    # F-beta with beta=1.5 (recall-weighted)
    beta_sq = 2.25  # 1.5^2
    if precision + recall > 0:
        f_beta = (1 + beta_sq) * precision * recall / (beta_sq * precision + recall)
    else:
        f_beta = 0.0

    base_score = f_beta * 0.85 + 0.10  # scale to [0.10, 0.95]

    # Seniority bonus: reward matching seniority, penalise mismatches
    seniority_bonus = 0.0
    jd_seniority_level = jd_profile.get("seniority_level", 2)
    for word in cand_words:
        if word in _SENIORITY_KEYWORDS:
            bonus = _SENIORITY_KEYWORDS[word]
            # Extra bonus if the JD also uses this seniority level
            if bonus > 0 and jd_seniority_level >= 3:
                seniority_bonus += bonus
            elif bonus < 0 and jd_seniority_level <= 1:
                seniority_bonus += abs(bonus)  # match: junior JD + junior candidate
            else:
                seniority_bonus += bonus * 0.5  # partial credit

    total = base_score + seniority_bonus
    return max(0.0, min(1.0, total))


# ---------------------------------------------------------------------------
# ML domain synonym expansion — maps a JD requirement to equivalent
# candidate skill names that mean the same thing
# ---------------------------------------------------------------------------
_ML_SYNONYMS: dict[str, set[str]] = {
    "machine learning": {
        "pytorch", "tensorflow", "keras", "scikit-learn", "sklearn",
        "xgboost", "lightgbm", "catboost", "mlflow", "ml",
        "model training", "feature engineering", "jax",
    },
    "deep learning": {
        "pytorch", "tensorflow", "keras", "neural network", "cnn",
        "rnn", "lstm", "transformer", "bert", "gpt", "jax",
    },
    "nlp": {
        "transformers", "bert", "gpt", "spacy", "nltk", "hugging face",
        "text classification", "named entity recognition", "ner",
        "natural language processing", "llm", "langchain",
    },
    "computer vision": {
        "opencv", "image classification", "object detection",
        "yolo", "cnn", "image segmentation", "detectron",
    },
    "mlops": {
        "mlflow", "kubeflow", "airflow", "docker", "kubernetes",
        "model deployment", "model serving", "ci/cd", "bentoml",
        "triton", "ray serve", "wandb",
    },
    "data science": {
        "python", "pandas", "numpy", "scipy", "jupyter", "r",
        "statistical modeling", "a/b testing", "sql",
    },
    "generative ai": {
        "llm", "gpt", "openai", "anthropic", "langchain", "rag",
        "stable diffusion", "fine-tuning", "prompt engineering",
    },
    # ── Non-ML domain synonyms for broader JD coverage ───────────
    "frontend": {
        "react", "angular", "vue", "svelte", "nextjs", "html", "css",
        "javascript", "typescript", "webpack", "vite", "tailwind",
    },
    "backend": {
        "nodejs", "express", "fastapi", "flask", "django", "spring",
        "rest api", "graphql", "microservices",
    },
    "devops": {
        "docker", "kubernetes", "terraform", "ansible", "ci/cd",
        "jenkins", "github actions", "aws", "gcp", "azure",
    },
    "data engineering": {
        "spark", "kafka", "airflow", "etl", "sql", "hadoop",
        "snowflake", "bigquery", "dbt", "data pipeline",
    },
    "cloud": {
        "aws", "gcp", "azure", "docker", "kubernetes",
        "ec2", "s3", "lambda", "terraform",
    },
    "mobile": {
        "ios", "android", "react native", "flutter", "swift",
        "kotlin", "swiftui", "jetpack compose",
    },
    "security": {
        "cybersecurity", "penetration testing", "owasp", "siem",
        "firewall", "encryption", "oauth", "jwt",
    },
}

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
    Lightweight TF-IDF replacement using term frequency overlap.

    Instead of scikit-learn's TfidfVectorizer (which was the #1 bottleneck),
    this computes a fast token-overlap score between each candidate's text
    and the JD tokens.  O(n * avg_tokens) but with small constant factors
    since it's pure set arithmetic.

    Returns a numpy array of scores in [0, 1], one per candidate.
    """
    global _debug_logged
    _debug_logged = False   # reset per request so first candidate always logs

    jd_tokens: set[str] = set(jd_profile.get("tokens") or [])
    jd_required: set[str] = jd_profile.get("required_skills") or set()
    if isinstance(jd_required, list):
        jd_required = set(jd_required)

    # Combine JD tokens + required skills + domain keywords for matching
    jd_terms = jd_tokens | jd_required
    domain_kw = jd_profile.get("domain_keywords") or []
    jd_terms |= set(domain_kw)

    if not jd_terms:
        return np.zeros(len(all_candidates))

    scores = np.zeros(len(all_candidates))

    for i, cand in enumerate(all_candidates):
        text = _candidate_to_text(cand)
        if not text:
            continue

        # Tokenize candidate text (simple split + lowercase)
        cand_words = set(text.lower().split())

        # Compute overlap
        overlap = len(cand_words & jd_terms)
        if overlap > 0:
            # Normalize by JD term count (recall-oriented)
            recall = overlap / len(jd_terms)
            scores[i] = min(recall * 2.0, 1.0)  # scale up, cap at 1.0

    return scores


def compute_semantic_score(candidate: dict, jd_profile: dict, tfidf_score: float) -> float:
    """
    JD-adaptive semantic relevance score in [0, 1].

    ALL components adapt to whatever JD is provided — not hardcoded to any
    specific domain.

    Component weights
    -----------------
    A) Title relevance          0.40  — word-overlap with JD title
    B) Skill relevance F1       0.30  — set intersection with synonym expansion
    C) TF-IDF cosine similarity 0.15  — fast token-overlap replacement
    D) Experience fit           0.10  — years vs JD requirement
    E) Seniority match          0.05  — level delta penalty
    """
    cand_skills: set[str] = candidate.get("skills_set") or set()
    jd_required: set[str] = jd_profile.get("required_skills") or set()
    jd_tokens: set[str]   = set(jd_profile.get("tokens") or [])
    jd_raw: str           = (jd_profile.get("raw_text") or "").lower()

    # ── A) Title relevance (0.40) ─────────────────────────────────────────
    title = candidate.get("current_title", "").lower()
    title_score = compute_title_score(title, jd_profile)

    title_component = title_score * 0.40

    # ── B) Skill relevance F1 with synonym expansion (0.30) ───────────────
    # Expand required skills with domain synonyms
    expanded_required: set[str] = set(jd_required)
    for core_skill, synonyms in _ML_SYNONYMS.items():
        if core_skill in jd_required or core_skill in jd_raw:
            expanded_required.update(synonyms)

    # Also pull skill_assessment_scores keys as additional candidate signals
    raw_signals: dict = (candidate.get("_raw") or {}).get("redrob_signals") or {}
    sa_keys: set[str] = {
        k.lower().replace("_", " ")
        for k in (raw_signals.get("skill_assessment_scores") or {}).keys()
    }
    combined_cand: set[str] = cand_skills | sa_keys

    if expanded_required and combined_cand:
        ov        = len(combined_cand & expanded_required)
        precision = ov / len(combined_cand)
        recall    = ov / len(expanded_required)
        f1        = 2 * precision * recall / (precision + recall) if (precision + recall) > 0 else 0.0
    else:
        ov  = 0
        f1  = 0.0
    skill_component = f1 * 0.30

    # ── C) TF-IDF / token-overlap similarity (0.15) ───────────────────────
    tfidf_component = float(np.clip(tfidf_score, 0.0, 1.0)) * 0.15

    # ── D) Experience fit (0.10) ──────────────────────────────────────────
    years     = candidate.get("years_experience") or 0
    min_years = jd_profile.get("min_years") or 3
    if years >= min_years:
        exp_score = min(1.0, years / max(min_years * 2, 8))
    else:
        exp_score = (years / max(min_years, 1)) * 0.7   # penalty for under-experienced
    exp_component = exp_score * 0.10

    # ── E) Seniority match (0.05) ─────────────────────────────────────────
    diff            = abs((candidate.get("seniority_level") or 2) - (jd_profile.get("seniority_level") or 3))
    seniority_score = max(0.0, 1.0 - diff * 0.25)
    sen_component   = seniority_score * 0.05

    total = title_component + skill_component + tfidf_component + exp_component + sen_component

    # ── Debug log for first candidate per request ─────────────────────────
    global _debug_logged
    if not _debug_logged:
        _debug_logged = True
        logger.debug(
            "SEMANTIC BREAKDOWN  "
            "title=%.3f×0.40=%.3f  "
            "skill_f1=%.3f×0.30=%.3f  "
            "tfidf=%.3f×0.15=%.3f  "
            "exp=%.3f×0.10=%.3f  "
            "seniority=%.3f×0.05=%.3f  "
            "→ total=%.4f  "
            "| cand_skills=%d  expanded_req=%d  overlap=%d  title=%r",
            title_score, title_component,
            f1, skill_component,
            float(np.clip(tfidf_score, 0.0, 1.0)), tfidf_component,
            exp_score, exp_component,
            seniority_score, sen_component,
            total,
            len(combined_cand), len(expanded_required), ov, title,
        )

    return round(float(np.clip(total, 0.0, 1.0)), 6)

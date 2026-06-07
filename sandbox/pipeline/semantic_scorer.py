"""
Semantic scorer for the TalentMind AI ranking pipeline.

Computes a composite semantic fitness score [0, 1] for each candidate
against a parsed JD profile, combining:

    Title overlap    (0.40)  — F-beta (β=1.5) recall-weighted
    Skill F1         (0.30)  — precision-recall with synonym expansion
    TF-IDF overlap   (0.15)  — token-level cosine from summary/headline
    Experience fit   (0.10)  — closeness to JD min_years
    Seniority match  (0.05)  — level delta penalty

All computation is offline — no embeddings or LLM calls.
"""

from __future__ import annotations

import math
from typing import Any, Dict, List, Optional, Set

import numpy as np

from sandbox.utils.text_utils import tokenize

# ──────────────────────────────────────────────────────────────────────
# Skill synonym groups for expansion (~20+ domain synonym clusters)
# ──────────────────────────────────────────────────────────────────────

_ML_SYNONYMS: Dict[str, List[str]] = {
    "machine learning": ["ml", "machine-learning", "statistical learning"],
    "deep learning": ["dl", "deep-learning", "neural networks", "neural network"],
    "natural language processing": ["nlp", "natural-language-processing", "text mining"],
    "computer vision": ["cv", "computer-vision", "image recognition", "image processing"],
    "pytorch": ["torch"],
    "tensorflow": ["tf"],
    "scikit-learn": ["sklearn", "scikit learn"],
    "kubernetes": ["k8s"],
    "docker": ["containerization", "containers"],
    "javascript": ["js"],
    "typescript": ["ts"],
    "react": ["reactjs", "react.js"],
    "angular": ["angularjs", "angular.js"],
    "vue": ["vuejs", "vue.js"],
    "node.js": ["nodejs", "node"],
    "postgresql": ["postgres", "psql"],
    "mongodb": ["mongo"],
    "amazon web services": ["aws"],
    "google cloud platform": ["gcp", "google-cloud"],
    "microsoft azure": ["azure"],
    "continuous integration": ["ci", "ci/cd", "cicd"],
    "large language models": ["llm", "llms"],
    "retrieval augmented generation": ["rag"],
    "mlops": ["ml-ops", "ml ops"],
    "data science": ["data-science"],
    "data engineering": ["data-engineering"],
    "hugging face": ["huggingface", "hugging-face", "hf"],
    "distributed training": ["distributed-training"],
    "reinforcement learning": ["rl", "reinforcement-learning"],
    "generative adversarial network": ["gan", "gans"],
    "convolutional neural network": ["cnn", "cnns"],
    "recurrent neural network": ["rnn", "rnns"],
    "transformer": ["transformers"],
}

# Build reverse map: synonym → canonical
_SYNONYM_LOOKUP: Dict[str, str] = {}
for canonical, syns in _ML_SYNONYMS.items():
    _SYNONYM_LOOKUP[canonical] = canonical
    for syn in syns:
        _SYNONYM_LOOKUP[syn] = canonical


def _expand_skills(skills: Set[str]) -> Set[str]:
    """Expand a skill set with all known synonyms (both directions)."""
    expanded = set(skills)
    for skill in skills:
        lower = skill.lower()
        # If this skill is a canonical or synonym, add all aliases
        if lower in _SYNONYM_LOOKUP:
            canon = _SYNONYM_LOOKUP[lower]
            expanded.add(canon)
            for syn_list in _ML_SYNONYMS.get(canon, []):
                expanded.add(syn_list)
        # Check if this skill appears as a synonym
        for canon, syns in _ML_SYNONYMS.items():
            if lower in (s.lower() for s in syns):
                expanded.add(canon)
                expanded |= set(s.lower() for s in syns)
    return expanded


# ──────────────────────────────────────────────────────────────────────
# Component scorers
# ──────────────────────────────────────────────────────────────────────

def compute_title_score(
    candidate_title: str,
    jd_title_keywords: Set[str],
) -> float:
    """
    F-beta (β=1.5, recall-weighted) overlap of title word tokens.

    Returns 0.0 if either title is empty.
    """
    if not candidate_title or not jd_title_keywords:
        return 0.0

    cand_tokens = set(tokenize(candidate_title))
    if not cand_tokens:
        return 0.0

    overlap = cand_tokens & jd_title_keywords
    if not overlap:
        return 0.0

    precision = len(overlap) / len(cand_tokens) if cand_tokens else 0.0
    recall = len(overlap) / len(jd_title_keywords) if jd_title_keywords else 0.0

    if precision + recall == 0:
        return 0.0

    beta = 1.5
    beta_sq = beta * beta
    fbeta = (1 + beta_sq) * precision * recall / (beta_sq * precision + recall)
    return min(fbeta, 1.0)


def compute_skill_f1(
    candidate_skills: Set[str],
    required_skills: Set[str],
    preferred_skills: Optional[Set[str]] = None,
) -> float:
    """
    Compute skill F1 score with synonym expansion.

    Weights required skills at 1.0 and preferred skills at 0.5.
    """
    if not required_skills and not preferred_skills:
        return 0.0
    if not candidate_skills:
        return 0.0

    # Expand both sides
    cand_expanded = _expand_skills(candidate_skills)
    req_expanded = _expand_skills(required_skills)
    pref_expanded = _expand_skills(preferred_skills or set())

    all_jd_skills = req_expanded | pref_expanded
    if not all_jd_skills:
        return 0.0

    # Matches
    req_matches = cand_expanded & req_expanded
    pref_matches = cand_expanded & pref_expanded

    # Weighted match count
    weighted_matches = len(req_matches) * 1.0 + len(pref_matches) * 0.5
    weighted_total = len(req_expanded) * 1.0 + len(pref_expanded) * 0.5

    if weighted_total == 0:
        return 0.0

    recall = weighted_matches / weighted_total
    precision = weighted_matches / len(cand_expanded) if cand_expanded else 0.0

    if precision + recall == 0:
        return 0.0

    f1 = 2.0 * precision * recall / (precision + recall)
    return min(f1, 1.0)


def compute_experience_score(
    candidate_years: float,
    jd_min_years: Optional[float],
) -> float:
    """
    Score experience fit as a bell-curve around JD min_years.

    Perfect score at min_years, gentle decay above/below.
    """
    if jd_min_years is None or jd_min_years <= 0:
        # No requirement — slight bonus for having some experience
        return min(candidate_years / 10.0, 1.0) if candidate_years > 0 else 0.3

    ratio = candidate_years / jd_min_years if jd_min_years > 0 else 1.0

    if ratio >= 0.8 and ratio <= 1.5:
        return 1.0
    elif ratio < 0.8:
        # Under-experienced
        return max(0.0, ratio / 0.8)
    else:
        # Over-experienced (gentle decay)
        return max(0.3, 1.0 - (ratio - 1.5) * 0.15)


def compute_seniority_score(
    candidate_level: int,
    jd_level: int,
) -> float:
    """Score seniority match. Perfect = same level, penalty per level delta."""
    delta = abs(candidate_level - jd_level)
    if delta == 0:
        return 1.0
    elif delta == 1:
        return 0.7
    elif delta == 2:
        return 0.3
    else:
        return 0.1


# ──────────────────────────────────────────────────────────────────────
# TF-IDF builder
# ──────────────────────────────────────────────────────────────────────

def build_tfidf_scorer(
    jd_profile: Dict[str, Any],
    candidates: List[Dict[str, Any]],
) -> np.ndarray:
    """
    Build token-overlap TF-IDF scores for all candidates against the JD.

    Uses a lightweight bag-of-words approach (no sklearn TfidfVectorizer
    dependency for this simple case — keeps it fast for 100k+ candidates).

    Parameters
    ----------
    jd_profile : dict
        Parsed JD profile.
    candidates : list[dict]
        Normalised candidate dicts.

    Returns
    -------
    np.ndarray of shape (len(candidates),) with scores in [0, 1].
    """
    jd_tokens = set(jd_profile.get("tokens", []))
    if not jd_tokens:
        return np.zeros(len(candidates), dtype=np.float64)

    # Document frequency for IDF
    n_docs = len(candidates) + 1  # +1 for JD doc
    doc_freq: Dict[str, int] = {}
    candidate_token_sets: List[set] = []

    for cand in candidates:
        cand_text = " ".join([
            cand.get("current_title", ""),
            cand.get("summary", ""),
            cand.get("headline", ""),
            " ".join(cand.get("skills_set", set())),
        ])
        tokens = set(tokenize(cand_text))
        candidate_token_sets.append(tokens)
        for tok in tokens:
            doc_freq[tok] = doc_freq.get(tok, 0) + 1

    # Compute IDF weights for JD tokens
    idf: Dict[str, float] = {}
    for tok in jd_tokens:
        df = doc_freq.get(tok, 0)
        idf[tok] = math.log((n_docs + 1) / (df + 1)) + 1.0

    # Score each candidate
    scores = np.zeros(len(candidates), dtype=np.float64)
    max_possible = sum(idf.values()) if idf else 1.0

    for i, cand_tokens in enumerate(candidate_token_sets):
        overlap = cand_tokens & jd_tokens
        score = sum(idf.get(tok, 0) for tok in overlap)
        scores[i] = score / max_possible if max_possible > 0 else 0.0

    return np.clip(scores, 0.0, 1.0)


# ──────────────────────────────────────────────────────────────────────
# Main composite scorer
# ──────────────────────────────────────────────────────────────────────

# Component weights
W_TITLE = 0.40
W_SKILL = 0.30
W_TFIDF = 0.15
W_EXP = 0.10
W_SENIORITY = 0.05


def compute_semantic_score(
    candidate: Dict[str, Any],
    jd_profile: Dict[str, Any],
    tfidf_score: float = 0.0,
) -> float:
    """
    Compute composite semantic fitness score [0, 1].

    Components:
        Title overlap    (0.40)
        Skill F1         (0.30)
        TF-IDF overlap   (0.15)
        Experience fit   (0.10)
        Seniority match  (0.05)
    """
    title_score = compute_title_score(
        candidate.get("current_title", ""),
        jd_profile.get("title_keywords", set()),
    )

    skill_score = compute_skill_f1(
        candidate.get("skills_set", set()),
        jd_profile.get("required_skills", set()),
        jd_profile.get("preferred_skills", set()),
    )

    exp_score = compute_experience_score(
        candidate.get("years_experience", 0),
        jd_profile.get("min_years"),
    )

    sen_score = compute_seniority_score(
        candidate.get("seniority_level", 2),
        jd_profile.get("seniority_level", 2),
    )

    composite = (
        W_TITLE * title_score
        + W_SKILL * skill_score
        + W_TFIDF * tfidf_score
        + W_EXP * exp_score
        + W_SENIORITY * sen_score
    )

    return min(max(composite, 0.0), 1.0)

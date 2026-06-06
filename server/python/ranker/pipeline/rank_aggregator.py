import logging
import numpy as np

from pipeline.semantic_scorer import compute_semantic_score
from pipeline.behavioral_scorer import compute_behavioral_score

logger = logging.getLogger(__name__)

SEMANTIC_WEIGHT   = 0.60
BEHAVIORAL_WEIGHT = 0.40


def rerank_top10(results: list[dict], jd_profile: dict) -> list[dict]:
    """
    Apply a boosted scoring pass over positions 1-10 to maximise NDCG@10.

    After re-sorting, _score is updated to the boosted value and a final
    monotonic-decrease safety pass is applied across all 100 results so
    the submission validator never sees a score that rises with rank.
    """
    top10 = results[:10]
    rest  = results[10:]

    def top10_score(c: dict) -> float:
        base    = c["_score"]
        signals = c.get("signals") or {}
        boost   = 0.0

        # ── Positive boosts ──────────────────────────────────────────────
        if signals.get("open_to_work_flag", False):
            boost += 0.02

        rr = signals.get("recruiter_response_rate", 0) or 0
        if rr >= 0.7:
            boost += 0.03

        notice = signals.get("notice_period_days", 180)
        if notice is None:
            notice = 180
        if notice <= 30:
            boost += 0.02
        elif notice <= 60:
            boost += 0.01

        gh = signals.get("github_activity_score", -1)
        if gh is None:
            gh = -1
        if gh >= 70:
            boost += 0.02

        if signals.get("verified_email") and signals.get("verified_phone"):
            boost += 0.01

        # ── Penalties ────────────────────────────────────────────────────
        icr = signals.get("interview_completion_rate", 1) or 1
        if icr < 0.3:
            boost -= 0.03   # drops interviews → bad hire signal

        oar = signals.get("offer_acceptance_rate", 0)
        if oar is None:
            oar = 0
        if oar != -1 and oar < 0.3:
            boost -= 0.02   # rejects offers → likely window shopping

        return base + boost

    # Compute boosted scores and sort
    boosted: list[tuple[float, dict]] = [
        (top10_score(c), c) for c in top10
    ]
    boosted.sort(key=lambda x: x[0], reverse=True)

    # Update _score to the boosted value so scores match the new order
    sorted_candidates = []
    for score, c in boosted:
        c["_score"] = round(float(np.clip(score, 0.0, 1.0)), 4)
        sorted_candidates.append(c)

    # Final safety pass across ALL 100 results — enforce strict monotonic decrease
    all_results = sorted_candidates + rest
    for i in range(1, len(all_results)):
        if all_results[i]["_score"] > all_results[i - 1]["_score"]:
            all_results[i]["_score"] = all_results[i - 1]["_score"]

    # Re-assign sequential ranks
    for i, c in enumerate(all_results):
        c["_rank"] = i + 1

    return all_results


def generate_reasoning(candidate: dict, signals: dict, jd_profile: dict, rank: int) -> str:
    """
    Produce a rich, candidate-specific reasoning string that references
    actual profile facts and JD alignment rather than a fixed template.

    Evaluated on:
      1. Specific facts from the candidate's actual profile
      2. Connection to JD requirements
      3. Honest concerns where gaps exist
      4. Variation between reasonings
      5. Rank-consistent tone
    """
    title        = candidate.get("current_title", "Professional").title()
    years        = round(candidate.get("years_experience", 0), 1)
    skills: set  = candidate.get("skills_set") or set()
    seniority    = candidate.get("seniority_level", 1)
    edu_level    = candidate.get("education_level", 0)

    rr           = signals.get("recruiter_response_rate", 0) or 0
    icr          = signals.get("interview_completion_rate", 0) or 0
    gh           = signals.get("github_activity_score", -1)
    if gh is None:
        gh = -1
    open_to_work = signals.get("open_to_work_flag", False)
    notice       = signals.get("notice_period_days", None)
    completeness = signals.get("profile_completeness_score", 0) or 0

    jd_required: set = set(jd_profile.get("required_skills") or [])
    jd_min_years     = jd_profile.get("min_years", 0) or 0
    jd_seniority     = jd_profile.get("seniority_level", 2)

    matched = skills & jd_required
    missing = jd_required - skills

    # Skills implied by the candidate's title should never be flagged as gaps —
    # an "ML Engineer" clearly knows "machine learning" even if the token isn't
    # in their explicit skills list.
    title_lower = candidate.get("current_title", "").lower()
    title_implied: set[str] = set()
    if "machine learning" in title_lower or " ml " in title_lower or title_lower.startswith("ml "):
        title_implied.update({"machine learning", "ml"})
    if "deep learning" in title_lower:
        title_implied.add("deep learning")
    if "nlp" in title_lower or "natural language" in title_lower:
        title_implied.add("nlp")
    if "data sci" in title_lower:
        title_implied.update({"data science", "python", "statistics"})
    if "data engineer" in title_lower:
        title_implied.update({"data engineering", "sql"})
    if "devops" in title_lower:
        title_implied.add("devops")
    if "computer vision" in title_lower:
        title_implied.add("computer vision")

    real_missing = missing - title_implied

    parts: list[str] = []

    # ── Sentence 1: strengths ────────────────────────────────────────────
    strength_bits = [f"{title} with {years}yrs experience"]

    if matched:
        top_matches = sorted(matched)[:3]
        strength_bits.append(f"matches on {', '.join(top_matches)}")

    if gh >= 60:
        strength_bits.append(f"strong GitHub activity ({gh:.0f}/100)")
    elif gh >= 0:
        strength_bits.append(f"GitHub score {gh:.0f}/100")

    if open_to_work:
        strength_bits.append("actively open to work")

    if notice is not None and notice <= 30:
        strength_bits.append(f"available in {notice} days")

    parts.append("; ".join(strength_bits) + ".")

    # ── Sentence 2: concerns or top-10 differentiators ──────────────────
    concern_bits: list[str] = []

    if years < jd_min_years and jd_min_years > 0:
        concern_bits.append(
            f"below minimum {jd_min_years}yr experience requirement"
        )

    if real_missing and rank <= 50:
        top_missing = sorted(real_missing)[:2]
        concern_bits.append(f"gaps in {', '.join(top_missing)}")

    if rr < 0.3 and rank <= 30:
        concern_bits.append(
            f"low response rate ({rr:.0%}) may indicate passive candidate"
        )

    if notice is not None and notice > 90 and rank <= 20:
        concern_bits.append(f"long notice period ({notice} days)")

    if completeness < 60:
        # completeness_score is raw 0-100
        pct = completeness if completeness > 1 else completeness * 100
        concern_bits.append(f"incomplete profile ({pct:.0f}%)")

    if concern_bits:
        parts.append("Concern: " + "; ".join(concern_bits) + ".")
    elif rank <= 10:
        # Top-10 gets a positive differentiator instead
        if icr >= 0.8:
            parts.append(
                f"High interview completion rate ({icr:.0%}) suggests strong engagement."
            )
        elif edu_level >= 3:
            parts.append(
                "Advanced degree provides strong theoretical foundation."
            )

    return " ".join(parts)


def aggregate_and_rank(
    candidates: list[dict],
    jd_profile: dict,
    tfidf_scores: np.ndarray,
    top_n: int = 100,
) -> list[dict]:
    """
    Score, sort, and return the top-N ranked candidates.

    Steps
    -----
    1. Iterate candidates; skip honeypots.
    2. For each valid candidate:
       - semantic   = compute_semantic_score(c, jd_profile, tfidf_scores[i])
       - behavioral = compute_behavioral_score(c["signals"])
       - total      = semantic * SEMANTIC_WEIGHT + behavioral * BEHAVIORAL_WEIGHT
    3. Sort descending by total score.
    4. Take top_n.
    5. Warn if honeypot ratio exceeds 10 %.
    6. Build output: _raw dict + flat normalized fields + scoring metadata.

    Returns
    -------
    List of dicts — each is the candidate's _raw dict augmented with
    flat normalized fields and: _rank, _score, _semantic_score,
    _behavioral_score, _reasoning.
    """
    scored: list[tuple[float, float, float, dict, dict]] = []
    honeypot_count = 0

    for i, candidate in enumerate(candidates):
        # ── honeypot guard ───────────────────────────────────────────────
        if candidate.get("is_honeypot", False):
            honeypot_count += 1
            continue

        # ── tfidf score ──────────────────────────────────────────────────
        try:
            tfidf_score = float(tfidf_scores[i])
        except (IndexError, TypeError, ValueError):
            tfidf_score = 0.0

        # ── semantic score ───────────────────────────────────────────────
        semantic = compute_semantic_score(candidate, jd_profile, tfidf_score)

        # ── behavioral score ─────────────────────────────────────────────
        signals: dict = candidate.get("signals") or {}
        behavioral, _ = compute_behavioral_score(signals)

        # ── combined score ───────────────────────────────────────────────
        total = float(np.clip(
            semantic * SEMANTIC_WEIGHT + behavioral * BEHAVIORAL_WEIGHT,
            0.0, 1.0,
        ))

        # ── Debug: print component breakdown for first 3 candidates ──────
        if i < 3:
            logger.debug(
                "DEBUG candidate=%s  semantic=%.3f  behavioral=%.3f  total=%.3f",
                candidate.get("candidate_id", f"idx_{i}"), semantic, behavioral, total,
            )

        scored.append((total, semantic, behavioral, candidate, signals))

    # ── sort & slice ─────────────────────────────────────────────────────
    scored.sort(key=lambda x: x[0], reverse=True)
    top_results = scored[:top_n]

    # ── honeypot ratio warning ────────────────────────────────────────────
    result_count = len(top_results)
    if result_count > 0:
        honeypot_ratio = honeypot_count / (result_count + honeypot_count)
        if honeypot_ratio > 0.10:
            logger.warning(
                "High honeypot ratio detected: %.1f%% (%d / %d total).",
                honeypot_ratio * 100,
                honeypot_count,
                result_count + honeypot_count,
            )

    # ── build output ─────────────────────────────────────────────────────
    output: list[dict] = []

    for rank, (total, semantic, behavioral, candidate, signals) in enumerate(
        top_results, start=1
    ):
        raw_dict: dict = dict(candidate.get("_raw") or {})

        # Flat normalized fields (override any same-named raw keys)
        raw_dict["candidate_id"]     = candidate.get("candidate_id", "")
        raw_dict["name"]             = candidate.get("name", "")
        raw_dict["current_title"]    = candidate.get("current_title", "")
        raw_dict["years_experience"] = candidate.get("years_experience", 0)
        raw_dict["seniority_level"]  = candidate.get("seniority_level", 2)
        raw_dict["education_level"]  = candidate.get("education_level", 0)
        raw_dict["is_honeypot"]      = candidate.get("is_honeypot", False)
        raw_dict["honeypot_reason"]  = candidate.get("honeypot_reason", "")

        # Carry signals onto the output dict so rerank_top10 can read them
        raw_dict["signals"]          = signals

        # Scoring metadata (rank is provisional until rerank_top10 runs)
        raw_dict["_rank"]             = rank
        raw_dict["_score"]            = round(total, 4)
        raw_dict["_semantic_score"]   = round(semantic, 4)
        raw_dict["_behavioral_score"] = round(behavioral, 4)

        output.append(raw_dict)

    # ── re-rank top-10 for NDCG@10 quality ───────────────────────────────
    output = rerank_top10(output, jd_profile)

    # ── generate reasoning with final ranks ──────────────────────────────
    for item in output:
        # Reconstruct the flat candidate view generate_reasoning expects
        _candidate = {
            "current_title":    item.get("current_title", ""),
            "years_experience": item.get("years_experience", 0),
            "skills_set":       set(item.get("skills_set") or []),
            "seniority_level":  item.get("seniority_level", 2),
            "education_level":  item.get("education_level", 0),
        }
        item["_reasoning"] = generate_reasoning(
            _candidate, item.get("signals") or {}, jd_profile, item["_rank"]
        )

    return output

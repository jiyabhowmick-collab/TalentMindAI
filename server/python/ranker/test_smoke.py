"""
Smoke test for the candidate normalizer + behavioral scorer.
Run from server/python/ranker/:
    python test_smoke.py

Uses a hand-crafted candidate that mirrors the real JSONL schema so we
can verify field access without needing the actual competition file.
If you have a real file, pass its path as the first CLI argument:
    python test_smoke.py /path/to/candidates.jsonl
"""

import json
import sys

sys.path.insert(0, ".")

from pipeline.candidate_normalizer import normalize_candidate
from pipeline.behavioral_scorer import compute_behavioral_score
from pipeline.honeypot_detector import is_honeypot

# ---------------------------------------------------------------------------
# Synthetic candidate matching the real schema
# ---------------------------------------------------------------------------
SYNTHETIC_CANDIDATE = {
    "candidate_id": "cand_001",
    "email": "ira.vora@example.com",
    "profile": {
        "anonymized_name": "Ira Vora",
        "current_title": "Senior Data Scientist",
        "years_of_experience": 6.9,
        "summary": (
            "Experienced data scientist with expertise in Python, machine learning, "
            "deep learning, and NLP. Proficient in scikit-learn, pandas, and PyTorch."
        ),
        "headline": "Senior Data Scientist | ML | Python | NLP",
        "location": "San Francisco, CA",
    },
    "skills": [
        {"name": "Python"},
        {"name": "Machine Learning"},
        {"name": "Deep Learning"},
        {"name": "NLP"},
        {"name": "PyTorch"},
        {"name": "scikit-learn"},
        {"name": "pandas"},
        {"name": "SQL"},
        {"name": "Docker"},
        {"name": "AWS"},
    ],
    "education": [
        {
            "degree": "Master of Science",
            "field_of_study": "Computer Science",
            "institution": "Stanford University",
            "graduation_year": 2019,
        }
    ],
    "redrob_signals": {
        "recruiter_response_rate": 0.82,
        "interview_completion_rate": 0.75,
        "profile_completeness_score": 88,
        "github_activity_score": 72,
        "offer_acceptance_rate": 0.67,
        "skill_assessment_scores": {
            "python": 91,
            "machine_learning": 85,
            "sql": 78,
        },
        "endorsements_received": 34,
        "connection_count": 410,
        "saved_by_recruiters_30d": 7,
        "profile_views_received_30d": 23,
        "open_to_work_flag": True,
        "verified_email": True,
        "verified_phone": False,
        "linkedin_connected": True,
        "signal_envelope_valid": True,
    },
}


def load_first_candidate(path: str) -> dict:
    """Load the first record from a JSONL or JSON file."""
    with open(path, encoding="utf-8") as f:
        content = f.read().strip()

    # Try JSON array first
    try:
        data = json.loads(content)
        if isinstance(data, list):
            return data[0]
        return data
    except json.JSONDecodeError:
        pass

    # Try JSONL (first non-empty line)
    for line in content.splitlines():
        line = line.strip()
        if line:
            return json.loads(line)

    raise ValueError("Could not parse any candidate from the file.")


def run_smoke_test(candidate: dict, label: str = "candidate") -> None:
    print(f"\n{'=' * 60}")
    print(f"  Smoke test: {label}")
    print(f"{'=' * 60}")

    # ── normalize ──────────────────────────────────────────────────
    norm = normalize_candidate(candidate)

    print(f"  name            : {norm['name']!r}")
    print(f"  current_title   : {norm['current_title']!r}")
    print(f"  years_experience: {norm['years_experience']}")
    print(f"  skills count    : {len(norm['skills_set'])}")
    print(f"  skills sample   : {sorted(norm['skills_set'])[:5]}")
    print(f"  seniority_level : {norm['seniority_level']}")
    print(f"  education_level : {norm['education_level']}")
    print(f"  is_honeypot     : {norm['is_honeypot']}  reason={norm['honeypot_reason']!r}")
    print(f"  signals keys    : {list(norm['signals'].keys())[:6]} ...")

    # ── behavioral score ───────────────────────────────────────────
    score, breakdown = compute_behavioral_score(norm["signals"])
    print(f"\n  behavioral_score: {round(score, 4)}")
    print("  breakdown:")
    for k, v in breakdown.items():
        bar = "█" * int(v * 20)
        print(f"    {k:<35s} {v:.4f}  {bar}")

    # ── assertions ────────────────────────────────────────────────
    errors = []
    if not norm["name"]:
        errors.append("FAIL: name is empty — check profile.anonymized_name path")
    if norm["years_experience"] == 0.0:
        errors.append("FAIL: years_experience is 0 — check profile.years_of_experience path")
    if not norm["skills_set"]:
        errors.append("FAIL: skills_set is empty — check skills[*].name path")
    if not norm["signals"]:
        errors.append("FAIL: signals is empty — check redrob_signals path")
    if score < 0.05:
        errors.append(f"FAIL: behavioral_score={score:.4f} is suspiciously low — signals not being read")

    if errors:
        print("\n  ❌ ISSUES FOUND:")
        for e in errors:
            print(f"     {e}")
        sys.exit(1)
    else:
        print("\n  ✅ All checks passed")


if __name__ == "__main__":
    if len(sys.argv) > 1:
        path = sys.argv[1]
        print(f"Loading first candidate from: {path}")
        try:
            real_candidate = load_first_candidate(path)
            run_smoke_test(real_candidate, label=f"real data ({path})")
        except Exception as e:
            print(f"Could not load real file: {e}")
            print("Falling back to synthetic candidate.\n")
            run_smoke_test(SYNTHETIC_CANDIDATE, label="synthetic (fallback)")
    else:
        run_smoke_test(SYNTHETIC_CANDIDATE, label="synthetic")

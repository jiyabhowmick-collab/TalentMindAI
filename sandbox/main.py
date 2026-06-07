"""
TalentMind AI — Sandbox CLI Entrypoint

Fully self-contained candidate ranking pipeline that runs offline.
Parses a job description, loads candidate JSONL data, applies pre-filtering,
semantic + behavioral scoring, and outputs a ranked shortlist.

Usage:
    python main.py --input candidates.jsonl --jd "Senior ML Engineer..."
    python main.py -i data/candidates.jsonl --top 50 --output results.csv
"""

from __future__ import annotations

import argparse
import csv
import json
import os
import sys
import time
from pathlib import Path
from typing import Any, Dict, List

# ── Ensure sandbox/ is importable ────────────────────────────────────
# When running as `python main.py` from inside sandbox/, we need the
# parent directory on sys.path so `from sandbox.xxx import ...` works.
_SANDBOX_DIR = Path(__file__).resolve().parent
_PROJECT_ROOT = _SANDBOX_DIR.parent
if str(_PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(_PROJECT_ROOT))

from sandbox.pipeline.jd_parser import parse_job_description
from sandbox.pipeline.candidate_normalizer import normalize_candidate
from sandbox.pipeline.honeypot_detector import is_honeypot
from sandbox.pipeline.prefilter import prefilter_candidates
from sandbox.pipeline.semantic_scorer import build_tfidf_scorer
from sandbox.pipeline.rank_aggregator import aggregate_and_rank, make_serializable

# ──────────────────────────────────────────────────────────────────────
# Default JD (used when --jd is not provided)
# ──────────────────────────────────────────────────────────────────────

DEFAULT_JD = """Senior Machine Learning Engineer

We are looking for a Senior ML Engineer with 5+ years of experience.
Required: Python, PyTorch, machine learning, deep learning, MLOps, Docker
Preferred: Kubernetes, MLflow, distributed training, LLMs, RAG
Must have: strong GitHub presence, experience deploying models to production
Nice to have: NLP, computer vision, Hugging Face transformers
"""


def main() -> None:
    """CLI entrypoint."""
    parser = argparse.ArgumentParser(
        description="TalentMind AI — Candidate Ranking Pipeline (Sandbox PoC)",
    )
    parser.add_argument(
        "--input", "-i",
        type=str,
        required=True,
        help="Path to input JSONL file with candidate records",
    )
    parser.add_argument(
        "--jd",
        type=str,
        default=None,
        help="Job description text (inline string). Uses a default ML Engineer JD if omitted.",
    )
    parser.add_argument(
        "--top", "-n",
        type=int,
        default=100,
        help="Number of top candidates to return (default: 100)",
    )
    parser.add_argument(
        "--output", "-o",
        type=str,
        default="results.csv",
        help="Output CSV file path (default: results.csv)",
    )

    args = parser.parse_args()

    # ── Validate input file exists ───────────────────────────────────
    input_path = Path(args.input)
    if not input_path.exists():
        parser.error(f"Input file not found: {args.input}")

    t_start = time.time()

    # ── Step 1: Parse JD ─────────────────────────────────────────────
    jd_text = args.jd if args.jd else DEFAULT_JD
    print("=" * 60)
    print("  TalentMind AI — Candidate Ranking Pipeline")
    print("=" * 60)
    print()

    jd_profile = parse_job_description(jd_text)
    print(f"[JD] Parsed: {len(jd_profile['required_skills'])} required skills, "
          f"{len(jd_profile['preferred_skills'])} preferred skills, "
          f"min {jd_profile['min_years'] or '?'}y experience, "
          f"seniority level {jd_profile['seniority_level']}")
    print(f"   Required: {', '.join(sorted(jd_profile['required_skills']))}")
    print(f"   Preferred: {', '.join(sorted(jd_profile['preferred_skills']))}")
    print()

    # ── Step 2: Load candidates from uploaded file ───────────────────
    raw_candidates, skipped = load_candidates_file(str(input_path))
    print(f"[LOAD] Loaded {len(raw_candidates)} candidates from {input_path.name}"
          + (f" ({skipped} invalid records skipped)" if skipped else ""))

    if not raw_candidates:
        print("[ERROR] No valid candidates found in the input file.")
        print("        File must be a JSON array of candidate objects,")
        print("        each with candidate_id and profile fields.")
        sys.exit(1)

    # ── Step 3: Normalize ────────────────────────────────────────────
    candidates = []
    for raw in raw_candidates:
        cand = normalize_candidate(raw)
        # Run honeypot detection
        flagged, reason = is_honeypot(cand)
        cand["is_honeypot"] = flagged
        cand["honeypot_reason"] = reason
        candidates.append(cand)

    honeypot_count = sum(1 for c in candidates if c["is_honeypot"])
    print(f"[DETECT] Honeypot detection: {honeypot_count} flagged")

    # ── Step 4: Pre-filter ───────────────────────────────────────────
    definite, possible, disqualified = prefilter_candidates(candidates, jd_profile)
    survivors = definite + possible
    print(f"[FILTER] Pre-filter: {len(definite)} definite + {len(possible)} possible = "
          f"{len(survivors)} survivors, {disqualified} discarded")

    if not survivors:
        print("[WARN] No survivors after pre-filter, using all non-honeypot candidates")
        survivors = [c for c in candidates if not c.get("is_honeypot", False)]

    # ── Step 5: Build TF-IDF scores ──────────────────────────────────
    print("[TFIDF] Computing TF-IDF scores...")
    tfidf_scores = build_tfidf_scorer(jd_profile, survivors)

    # ── Step 6: Aggregate & Rank ─────────────────────────────────────
    print("[RANK] Ranking candidates...")
    top_n = min(args.top, len(survivors))
    ranked = aggregate_and_rank(survivors, jd_profile, tfidf_scores, top_n)

    t_elapsed = time.time() - t_start

    # ── Step 7: Output ───────────────────────────────────────────────
    print()
    print("=" * 60)
    print(f"  TOP {min(10, len(ranked))} CANDIDATES (of {len(ranked)} ranked)")
    print("=" * 60)
    print()

    for entry in ranked[:10]:
        _print_candidate(entry)

    # ── Write CSV ────────────────────────────────────────────────────
    output_path = args.output
    _write_csv(ranked, output_path)
    print(f"\n[CSV] Full results written to: {output_path}")
    print(f"[DONE] Completed in {t_elapsed:.2f}s")
    print()


# ──────────────────────────────────────────────────────────────────────
# Data loading
# ──────────────────────────────────────────────────────────────────────

def _is_valid_candidate(obj: Any) -> bool:
    """Check that a parsed object is a dict with at least candidate_id and profile."""
    return (
        isinstance(obj, dict)
        and "candidate_id" in obj
        and "profile" in obj
    )


def load_candidates_file(filepath: str) -> tuple[List[Dict[str, Any]], int]:
    """
    Load candidates from a .json or .jsonl file.

    .json  — root may be an array of candidates, or an object with a
             "candidates" key pointing to an array.
    .jsonl — one JSON object per line (with concatenated-object fallback).

    Each record is validated: must be a dict with candidate_id and profile.
    Invalid records are skipped with a warning count.

    Returns
    -------
    (candidates, skipped_count)
    """
    ext = Path(filepath).suffix.lower()

    if ext == ".json":
        return _load_json(filepath)
    elif ext in (".jsonl", ".ndjson"):
        return _load_jsonl(filepath)
    else:
        # Try JSON first, fall back to JSONL
        try:
            return _load_json(filepath)
        except (json.JSONDecodeError, UnicodeDecodeError):
            return _load_jsonl(filepath)


def _load_json(filepath: str) -> tuple[List[Dict[str, Any]], int]:
    """Load candidates from a standard .json file."""
    with open(filepath, "r", encoding="utf-8-sig") as f:
        data = json.load(f)

    # Determine where the candidate list is
    raw_list: List[Any]
    if isinstance(data, list):
        # Root is an array → use directly
        raw_list = data
    elif isinstance(data, dict):
        # Root is an object → look for a "candidates" key
        if "candidates" in data and isinstance(data["candidates"], list):
            raw_list = data["candidates"]
        elif "data" in data and isinstance(data["data"], list):
            raw_list = data["data"]
        else:
            # Single candidate object? Wrap it.
            raw_list = [data]
    else:
        return [], 0

    # Validate each record
    candidates: List[Dict[str, Any]] = []
    skipped = 0
    for item in raw_list:
        if _is_valid_candidate(item):
            candidates.append(item)
        elif isinstance(item, dict):
            # Dict but missing required fields — still usable if it has *some* data
            # Accept dicts that at least look like candidate records
            if item.get("profile") or item.get("skills") or item.get("redrob_signals"):
                # Assign a synthetic ID if missing
                if "candidate_id" not in item:
                    item["candidate_id"] = f"UNKNOWN_{skipped + len(candidates)}"
                if "profile" not in item:
                    item["profile"] = {}
                candidates.append(item)
            else:
                skipped += 1
        else:
            skipped += 1

    if skipped > 0:
        print(f"[WARN] Skipped {skipped} invalid records in JSON file")
    return candidates, skipped


def _parse_jsonl_line(line: str) -> List[Dict[str, Any]]:
    """
    Handle lines that may contain multiple concatenated JSON objects.

    e.g. '{"a":1}{"b":2}' on a single line -> [{"a":1}, {"b":2}]
    Also filters out non-dict values (bare strings, numbers, arrays).
    """
    results: List[Dict[str, Any]] = []
    decoder = json.JSONDecoder()
    pos = 0
    line = line.strip()
    while pos < len(line):
        try:
            obj, end_pos = decoder.raw_decode(line, pos)
            if isinstance(obj, dict):
                results.append(obj)
            pos = end_pos
            # skip whitespace between objects
            while pos < len(line) and line[pos] in " \t":
                pos += 1
        except json.JSONDecodeError:
            break
    return results


def _load_jsonl(filepath: str) -> tuple[List[Dict[str, Any]], int]:
    """Load candidates from a JSONL file (one JSON object per line)."""
    candidates: List[Dict[str, Any]] = []
    skipped = 0
    with open(filepath, "r", encoding="utf-8-sig") as f:
        for line_num, line in enumerate(f, 1):
            line = line.strip()
            if not line:
                continue
            parsed = _parse_jsonl_line(line)
            for obj in parsed:
                if _is_valid_candidate(obj):
                    candidates.append(obj)
                elif isinstance(obj, dict) and (obj.get("profile") or obj.get("skills")):
                    if "candidate_id" not in obj:
                        obj["candidate_id"] = f"LINE_{line_num}"
                    if "profile" not in obj:
                        obj["profile"] = {}
                    candidates.append(obj)
                else:
                    skipped += 1
            if not parsed:
                skipped += 1
                if skipped <= 5:
                    print(f"[WARN] Skipping malformed line {line_num}")
    if skipped > 5:
        print(f"[WARN] ... and {skipped - 5} more malformed lines skipped")
    return candidates, skipped


# Keep backward-compatible alias
def load_jsonl(filepath: str) -> List[Dict[str, Any]]:
    """Legacy wrapper — use load_candidates_file() instead."""
    candidates, _ = load_candidates_file(filepath)
    return candidates


# ──────────────────────────────────────────────────────────────────────
# Output formatting
# ──────────────────────────────────────────────────────────────────────

def _print_candidate(entry: Dict[str, Any]) -> None:
    """Print a single ranked candidate to stdout."""
    rank = entry.get("rank", "?")
    cid = entry.get("candidate_id", "?")
    name = entry.get("name", "?")
    title = entry.get("current_title", "?")
    score = entry.get("_score", 0)
    sem = entry.get("semantic_score", 0)
    beh = entry.get("behavioral_score", 0)
    reasoning = entry.get("reasoning", "")

    print(f"  #{rank:>2}  {name:<20s}  {title:<35s}  Score: {score:.4f}")
    print(f"       Semantic: {sem:.4f}  |  Behavioral: {beh:.4f}")
    print(f"       {reasoning}")
    print()


def _write_csv(ranked: List[Dict[str, Any]], output_path: str) -> None:
    """Write ranked candidates to CSV."""
    fieldnames = [
        "rank", "candidate_id", "score", "semantic_score",
        "behavioral_score", "reasoning",
    ]

    with open(output_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        for entry in ranked:
            row = {
                "rank": entry.get("rank", ""),
                "candidate_id": entry.get("candidate_id", ""),
                "score": entry.get("_score", 0),
                "semantic_score": entry.get("semantic_score", 0),
                "behavioral_score": entry.get("behavioral_score", 0),
                "reasoning": entry.get("reasoning", ""),
            }
            writer.writerow(row)


if __name__ == "__main__":
    main()

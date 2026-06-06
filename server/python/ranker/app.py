import uuid
import gzip
import json
import io
import csv
import logging
import traceback

from flask import Flask, request, jsonify, Response
from flask_cors import CORS

from pipeline.jd_parser import parse_job_description
from pipeline.candidate_normalizer import normalize_candidate
from pipeline.semantic_scorer import build_tfidf_scorer, compute_semantic_score
from pipeline.behavioral_scorer import compute_behavioral_score
from pipeline.rank_aggregator import aggregate_and_rank

# ── Logging ─────────────────────────────────────────────────────────
logging.basicConfig(
    level=logging.DEBUG,
    format="[%(asctime)s] %(levelname)s %(name)s: %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger("ranker")

app = Flask(__name__)
CORS(app)

# In-memory cache: { job_id: { "total_candidates": int, "results": list[dict] } }
results_cache: dict[str, dict] = {}


def make_serializable(obj):
    """
    Recursively convert non-JSON-serializable types (set, numpy types, etc.)
    so Flask's jsonify never chokes.
    """
    import numpy as np
    if isinstance(obj, set):
        return sorted(obj)           # set → sorted list for determinism
    if isinstance(obj, (np.integer,)):
        return int(obj)
    if isinstance(obj, (np.floating,)):
        return float(obj)
    if isinstance(obj, np.ndarray):
        return obj.tolist()
    if isinstance(obj, dict):
        return {k: make_serializable(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [make_serializable(i) for i in obj]
    return obj


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def parse_jsonl_file(file_bytes: bytes) -> list[dict]:
    """
    Parse a JSONL (or gzip-compressed JSONL) byte payload into a list of dicts.
    Invalid lines are silently skipped.
    """
    try:
        data = gzip.decompress(file_bytes)
        logger.debug("File decompressed as gzip")
    except Exception:
        data = file_bytes
        logger.debug("File treated as plain JSONL")

    lines = data.decode("utf-8", errors="ignore").strip().split("\n")
    candidates: list[dict] = []

    for i, line in enumerate(lines):
        line = line.strip()
        if not line:
            continue
        try:
            candidates.append(json.loads(line))
        except json.JSONDecodeError as e:
            logger.warning("Skipping invalid JSON on line %d: %s", i + 1, e)
            continue

    logger.info("Parsed %d candidates from %d lines", len(candidates), len(lines))
    return candidates


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------

@app.route("/rank", methods=["POST"])
def rank():
    try:
        if "file" not in request.files:
            return jsonify({"error": "No file uploaded"}), 400

        jd_text = request.form.get("job_description", "")
        if not jd_text:
            return jsonify({"error": "No job description"}), 400

        file_bytes = request.files["file"].read()
        logger.info("Received file: %s (%d bytes)", request.files["file"].filename, len(file_bytes))

        # 1. Parse raw candidates from JSONL / JSONL.GZ
        raw_candidates = parse_jsonl_file(file_bytes)
        if not raw_candidates:
            return jsonify({"error": "No valid candidates parsed"}), 400

        # 2. Parse JD into a structured profile
        logger.info("Parsing job description (%d chars)...", len(jd_text))
        jd_profile = parse_job_description(jd_text)
        # Convert sets to lists so jd_profile is serializable downstream
        jd_profile["required_skills"] = set(jd_profile.get("required_skills") or [])
        jd_profile["preferred_skills"] = set(jd_profile.get("preferred_skills") or [])
        logger.debug("JD seniority=%d  min_years=%.1f  required_skills=%d",
                     jd_profile["seniority_level"], jd_profile["min_years"],
                     len(jd_profile["required_skills"]))

        # 3. Normalize every candidate
        logger.info("Normalizing %d candidates...", len(raw_candidates))
        normalized = [normalize_candidate(c) for c in raw_candidates]
        honeypots = sum(1 for c in normalized if c.get("is_honeypot"))
        logger.info("Normalization done. Honeypots detected: %d", honeypots)

        # ── DEBUG: diagnose skill overlap quality ────────────────────────
        if normalized:
            # Pick first non-honeypot candidate as the debug subject
            debug_c = next((c for c in normalized if not c.get("is_honeypot")), normalized[0])
            skills_sample = sorted(debug_c.get("skills_set") or set())
            jd_req        = sorted(jd_profile.get("required_skills") or set())
            overlap        = set(skills_sample) & set(jd_req)
            logger.debug("─── SKILL OVERLAP DIAGNOSIS ───────────────────────────")
            logger.debug("  candidate     : %s (%s)", debug_c.get("name"), debug_c.get("current_title"))
            logger.debug("  skills_set    : %d items → %s", len(skills_sample), skills_sample[:10])
            logger.debug("  jd required   : %d items → %s", len(jd_req), jd_req[:10])
            logger.debug("  overlap       : %d → %s", len(overlap), sorted(overlap))
            logger.debug("  signals keys  : %s", list((debug_c.get("signals") or {}).keys()))
            logger.debug("───────────────────────────────────────────────────────")

        # 4. Build TF-IDF scorer (batch — fits on the whole pool at once)
        logger.info("Building TF-IDF matrix...")
        tfidf_scores = build_tfidf_scorer(jd_profile, normalized)
        logger.info("TF-IDF done. Score range: %.4f – %.4f", float(tfidf_scores.min()), float(tfidf_scores.max()))

        # 5. Aggregate scores and rank
        logger.info("Ranking candidates...")
        results = aggregate_and_rank(normalized, jd_profile, tfidf_scores, top_n=100)
        logger.info("Ranking done. Returning %d results.", len(results))

        # 6. Make results JSON-serializable (sets → lists, numpy types → Python)
        results = make_serializable(results)

        # 7. Cache and return
        job_id = str(uuid.uuid4())
        results_cache[job_id] = {
            "total_candidates": len(raw_candidates),
            "results": results,
        }

        logger.info("Job %s complete.", job_id)
        return jsonify({
            "job_id": job_id,
            "total_candidates": len(raw_candidates),
            "returned": len(results),
            "message": "Ranking complete",
        })

    except Exception as e:
        logger.error("Error in /rank:\n%s", traceback.format_exc())
        return jsonify({"error": str(e)}), 500


@app.route("/results/<job_id>", methods=["GET"])
def get_results(job_id: str):
    """
    Returns the full ranked results for a previously submitted job.
    """
    if job_id not in results_cache:
        return jsonify({"error": "Job not found"}), 404

    cached = results_cache[job_id]
    return jsonify({
        "job_id": job_id,
        "total_candidates": cached["total_candidates"],
        "returned": len(cached["results"]),
        "results": cached["results"],
    })


@app.route("/export/<job_id>/<int:tier>", methods=["GET"])
def export_csv(job_id: str, tier: int):
    """
    Exports the top-N results for a job as a CSV file.
    Allowed tiers: 10, 50, 100.

    CSV columns: candidate_id, rank, score, reasoning
    """
    if job_id not in results_cache:
        return jsonify({"error": "Job not found"}), 404

    if tier not in (10, 50, 100):
        return jsonify({"error": "Tier must be 10, 50, or 100"}), 400

    results = results_cache[job_id]["results"][:tier]

    output = io.StringIO()
    writer = csv.DictWriter(
        output,
        fieldnames=["candidate_id", "rank", "score", "reasoning"],
    )
    writer.writeheader()

    for r in results:
        # candidate_id may live at top level or inside _raw
        candidate_id = r.get("candidate_id") or r.get("_raw", {}).get("candidate_id", "")
        writer.writerow({
            "candidate_id": candidate_id,
            "rank":         r["_rank"],
            "score":        r["_score"],
            "reasoning":    r["_reasoning"],
        })

    filename = f"talent-mind_top-{tier}_{job_id[:8]}.csv"
    return Response(
        output.getvalue(),
        mimetype="text/csv",
        headers={"Content-Disposition": f"attachment; filename={filename}"},
    )


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    logger.info("Starting TalentMind ranker on http://localhost:5000")
    app.run(port=5000, debug=True, use_reloader=True)

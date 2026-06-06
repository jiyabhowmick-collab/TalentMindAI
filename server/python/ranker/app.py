"""
TalentMind Ranker — Flask orchestrator (speed-optimised).

Run from server/python/ranker/:
    python app.py

NEVER run as:
    python server/python/ranker/app.py
because relative imports ("from pipeline.X") break when cwd != the ranker dir.
"""

# ── ISSUE 4: ensure cwd is always the directory containing this file ─────────
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import uuid
import gzip
import json
import io
import csv
import logging
import traceback
import threading
import time
from concurrent.futures import ThreadPoolExecutor

import numpy as np
from flask import Flask, request, jsonify, Response
from flask_cors import CORS

# ── Logging (set up BEFORE imports so import errors are captured) ─────────────
logging.basicConfig(
    level=logging.DEBUG,
    format="[%(asctime)s] %(levelname)s %(name)s: %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger("ranker")

# ── ISSUE 1: wrap pipeline imports so a broken module never kills Flask ───────
try:
    from pipeline.jd_parser import parse_job_description
    from pipeline.candidate_normalizer import normalize_candidate
    from pipeline.semantic_scorer import build_tfidf_scorer, compute_semantic_score
    from pipeline.behavioral_scorer import compute_behavioral_score
    from pipeline.rank_aggregator import aggregate_and_rank
    from pipeline.prefilter import prefilter_candidates
    PIPELINE_READY = True
    logger.info("Pipeline imports OK")
except Exception as _import_err:
    logger.error("[STARTUP ERROR] Pipeline import failed: %s", _import_err)
    traceback.print_exc()
    PIPELINE_READY = False

# ── App ───────────────────────────────────────────────────────────────────────
app = Flask(__name__)
CORS(app)

# In-memory cache: { job_id: { "total_candidates": int, "results": list[dict] } }
results_cache: dict[str, dict] = {}

# Progress cache: { job_id: { "step": int, "message": str, "total": int } }
# steps: 1=parsing  2=pre-filtering  3=normalizing+tfidf  4=ranking  5=done
progress_cache: dict[str, dict] = {}

# Thread pool for parallel JSONL parsing — created once at module level
_CPU_COUNT = os.cpu_count() or 4
_PARSE_POOL = ThreadPoolExecutor(max_workers=_CPU_COUNT)


def _set_progress(job_id: str, step: int, message: str, total: int = 0) -> None:
    progress_cache[job_id] = {"step": step, "message": message, "total": total}
    logger.info("[%s] step=%d %s", job_id, step, message)


# ---------------------------------------------------------------------------
# ISSUE 3: catch-all 404 handler — shows registered routes for easy debugging
# ---------------------------------------------------------------------------
@app.errorhandler(404)
def not_found(e):
    rules = [str(r) for r in app.url_map.iter_rules()]
    return jsonify({"error": "404 Not Found", "registered_routes": sorted(rules)}), 404


@app.errorhandler(405)
def method_not_allowed(e):
    return jsonify({"error": "405 Method Not Allowed", "message": str(e)}), 405


# ---------------------------------------------------------------------------
# Gzip response compression — speeds up HTTP transfer of 100-result JSON
# ---------------------------------------------------------------------------
@app.after_request
def compress_response(response):
    if (response.status_code == 200 and
        response.content_type and
        response.content_type.startswith('application/json') and
        len(response.data) > 1000):
        accept_encoding = request.headers.get('Accept-Encoding', '')
        if 'gzip' in accept_encoding:
            compressed = gzip.compress(response.data, compresslevel=1)
            if len(compressed) < len(response.data):
                response.data = compressed
                response.headers['Content-Encoding'] = 'gzip'
                response.headers['Content-Length'] = len(compressed)
    return response


# ---------------------------------------------------------------------------
# ISSUE 2: health + index routes registered BEFORE any pipeline code
# ---------------------------------------------------------------------------
@app.route("/", methods=["GET"])
def index():
    return jsonify({
        "service":        "talentmind-ranker",
        "status":         "ok",
        "pipeline_ready": PIPELINE_READY,
        "routes": [
            "GET  /",
            "GET  /health",
            "POST /rank",
            "GET  /results/<job_id>",
            "GET  /export/<job_id>/<tier>",
        ],
    })


@app.route("/health", methods=["GET"])
def health():
    return jsonify({
        "status":         "ok",
        "pipeline_ready": PIPELINE_READY,
        "service":        "talentmind-ranker",
    })


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def make_serializable(obj):
    """Recursively convert non-JSON-serializable types."""
    if isinstance(obj, set):
        return sorted(obj)
    if isinstance(obj, np.integer):
        return int(obj)
    if isinstance(obj, np.floating):
        return float(obj)
    if isinstance(obj, np.ndarray):
        return obj.tolist()
    if isinstance(obj, dict):
        return {k: make_serializable(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [make_serializable(i) for i in obj]
    return obj


def _parse_chunk(lines: list[bytes]) -> list[dict]:
    """Parse a chunk of JSONL byte-lines into dicts. Used by thread pool."""
    result = []
    for line in lines:
        line = line.strip()
        if not line:
            continue
        try:
            result.append(json.loads(line))
        except Exception:
            continue
    return result


def parse_jsonl_parallel(file_bytes: bytes) -> list[dict]:
    """
    Parse JSONL or gzip-compressed JSONL bytes into a list of dicts.

    Uses ThreadPoolExecutor for parallel chunk parsing.  Threads beat
    processes here because json.loads releases the GIL during C-extension
    work (the json module is implemented in C).
    """
    # Decompress if gzipped
    try:
        data = gzip.decompress(file_bytes)
        logger.debug("File decompressed as gzip")
    except Exception:
        data = file_bytes
        logger.debug("File treated as plain JSONL")

    # Split into lines (bytes — avoids full UTF-8 decode)
    lines = data.split(b'\n')
    total = len(lines)

    # Chunk into CPU-count groups for parallel parsing
    chunk_size = max(total // _CPU_COUNT, 1000)
    chunks = [
        lines[i:i + chunk_size]
        for i in range(0, total, chunk_size)
    ]

    # Parse chunks in parallel threads
    candidates: list[dict] = []
    futures = [_PARSE_POOL.submit(_parse_chunk, chunk) for chunk in chunks]
    for f in futures:
        candidates.extend(f.result())

    logger.info("Parsed %d candidates from %d lines (%d chunks)",
                len(candidates), total, len(chunks))
    return candidates


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------

@app.route("/status/<job_id>", methods=["GET"])
def get_status(job_id: str):
    """
    Returns granular pipeline progress for a job.
    Frontend polls this to advance steps 1 and 2 before results are ready.
    """
    if job_id in results_cache:
        # Job is fully done — also return from here
        return jsonify({
            "job_id":  job_id,
            "step":    5,
            "message": "Done",
            "total":   results_cache[job_id]["total_candidates"],
            "done":    True,
        })
    if job_id not in progress_cache:
        return jsonify({"error": "Job not found"}), 404
    p = progress_cache[job_id]
    return jsonify({
        "job_id":  job_id,
        "step":    p["step"],
        "message": p["message"],
        "total":   p["total"],
        "done":    False,
    })


@app.route("/rank", methods=["POST"])
def rank():
    if not PIPELINE_READY:
        return jsonify({"error": "Pipeline failed to load at startup — check server logs"}), 503

    try:
        if "file" not in request.files:
            return jsonify({"error": "No file uploaded"}), 400

        jd_text = request.form.get("job_description", "")
        if not jd_text:
            return jsonify({"error": "No job description"}), 400

        file_bytes = request.files["file"].read()
        logger.info("Received file: %s (%d bytes)",
                    request.files["file"].filename, len(file_bytes))

        # Generate job_id immediately and return it — processing runs in background
        job_id = str(uuid.uuid4())
        _set_progress(job_id, 1, "Parsing candidates...", 0)

        thread = threading.Thread(
            target=_run_pipeline,
            args=(job_id, file_bytes, jd_text),
            daemon=True,
        )
        thread.start()

        return jsonify({
            "job_id":  job_id,
            "message": "Job accepted, processing started",
        })

    except Exception:
        logger.error("Error in /rank:\n%s", traceback.format_exc())
        return jsonify({"error": traceback.format_exc().splitlines()[-1]}), 500


def _run_pipeline(job_id: str, file_bytes: bytes, jd_text: str) -> None:
    """
    3-phase background pipeline:

      Phase 1:  Parse JSONL (parallel) → parse JD → cheap pre-filter
      Phase 2:  Normalise survivors only → token-overlap scoring
      Phase 3:  Full scoring → heapq top-100 → rerank → output
    """
    try:
        t0 = time.perf_counter()

        # ── Phase 1a: Parse candidates (parallel) ─────────────────────────
        _set_progress(job_id, 1, "Parsing candidates...", 0)
        raw_candidates = parse_jsonl_parallel(file_bytes)
        if not raw_candidates:
            progress_cache[job_id] = {"step": -1, "message": "No valid candidates parsed", "total": 0}
            return

        total = len(raw_candidates)
        t1 = time.perf_counter()
        _set_progress(job_id, 1, f"Parsed {total} candidates in {t1-t0:.1f}s", total)

        # ── Phase 1b: Parse JD ────────────────────────────────────────────
        jd_profile = parse_job_description(jd_text)
        jd_profile["required_skills"] = set(jd_profile.get("required_skills") or [])
        jd_profile["preferred_skills"] = set(jd_profile.get("preferred_skills") or [])

        # ── Phase 1c: Cheap pre-filter (on raw dicts, BEFORE normalisation)
        _set_progress(job_id, 2, "Pre-filtering candidates...", total)
        definite, possible, disqualified_count = prefilter_candidates(raw_candidates, jd_profile)
        survivors = definite + possible
        t2 = time.perf_counter()
        _set_progress(
            job_id, 2,
            f"Pre-filter: {len(survivors)} survivors, {disqualified_count} eliminated in {t2-t1:.1f}s",
            total,
        )

        if not survivors:
            # If pre-filter eliminated everything, fall back to normalising all
            logger.warning("[%s] Pre-filter eliminated ALL candidates — falling back to full pipeline", job_id)
            survivors = raw_candidates

        # ── Phase 2a: Normalise survivors only ────────────────────────────
        _set_progress(job_id, 3, f"Normalizing {len(survivors)} candidates...", total)
        normalized = [normalize_candidate(c) for c in survivors]
        honeypots = sum(1 for c in normalized if c.get("is_honeypot"))
        t3 = time.perf_counter()
        logger.info("[%s] Normalization done (%d candidates, %d honeypots) in %.1fs",
                    job_id, len(normalized), honeypots, t3-t2)

        # ── Phase 2b: Token-overlap scoring (lightweight TF-IDF replacement)
        _set_progress(job_id, 3, "Building token-overlap scores...", total)
        tfidf_scores = build_tfidf_scorer(jd_profile, normalized)
        t3b = time.perf_counter()
        logger.info("[%s] Token-overlap done. Score range: %.4f – %.4f in %.1fs",
                    job_id, float(tfidf_scores.min()), float(tfidf_scores.max()), t3b-t3)

        # ── Phase 3: Score + heapq top-100 + rerank ──────────────────────
        _set_progress(job_id, 4, f"Ranking {len(normalized)} candidates...", total)
        results = aggregate_and_rank(normalized, jd_profile, tfidf_scores, top_n=100)
        t4 = time.perf_counter()
        logger.info("[%s] Ranking done. %d results in %.1fs", job_id, len(results), t4-t3b)

        # ── Serialise + cache (marking job done) ─────────────────────────
        results = make_serializable(results)
        results_cache[job_id] = {
            "total_candidates": total,
            "results":          results,
        }

        t_total = time.perf_counter() - t0
        _set_progress(job_id, 5, f"Done in {t_total:.1f}s", total)
        logger.info(
            "[%s] Job complete in %.1fs  "
            "(parse=%.1fs, filter=%.1fs, norm=%.1fs, tfidf=%.1fs, rank=%.1fs)  "
            "| %d total -> %d survivors -> %d results",
            job_id, t_total, t1-t0, t2-t1, t3-t2, t3b-t3, t4-t3b,
            total, len(normalized), len(results),
        )

    except Exception:
        logger.error("[%s] Pipeline error:\n%s", job_id, traceback.format_exc())
        progress_cache[job_id] = {
            "step":    -1,
            "message": traceback.format_exc().splitlines()[-1],
            "total":   0,
        }


@app.route("/results/<job_id>", methods=["GET"])
def get_results(job_id: str):
    if job_id not in results_cache:
        return jsonify({"error": "Job not found"}), 404
    cached = results_cache[job_id]
    return jsonify({
        "job_id":           job_id,
        "total_candidates": cached["total_candidates"],
        "returned":         len(cached["results"]),
        "results":          cached["results"],
    })


@app.route("/export/<job_id>/<int:tier>", methods=["GET"])
def export_csv(job_id: str, tier: int):
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
    logger.info("pipeline_ready=%s", PIPELINE_READY)
    app.run(host="0.0.0.0", port=5000, debug=True, use_reloader=True)

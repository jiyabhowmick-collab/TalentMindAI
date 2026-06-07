"""
TalentMind AI — Lightweight Flask Demo UI

Web interface for the candidate ranking pipeline.
Upload a JSON file with candidates, enter a JD, and view ranked results.

Run with:
    python demo_server.py

Then open http://localhost:5000 in a browser.
"""

from __future__ import annotations

import json
import os
import sys
import time
from pathlib import Path
from typing import Any, Dict, List

from flask import Flask, render_template_string, request, jsonify

# ── Ensure sandbox/ is importable ────────────────────────────────────
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
from sandbox.main import load_candidates_file, DEFAULT_JD

# ── Upload folder ────────────────────────────────────────────────────
UPLOAD_DIR = _SANDBOX_DIR / "uploads"
UPLOAD_DIR.mkdir(exist_ok=True)

ALLOWED_EXTENSIONS = {".json", ".jsonl"}

app = Flask(__name__)
app.config["MAX_CONTENT_LENGTH"] = 500 * 1024 * 1024  # 500 MB max upload

# ──────────────────────────────────────────────────────────────────────
# HTML Template (self-contained — no separate templates directory)
# ──────────────────────────────────────────────────────────────────────

HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>TalentMind AI — Candidate Ranker</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body {
            font-family: 'Segoe UI', system-ui, -apple-system, sans-serif;
            background: #0f1117;
            color: #e1e4e8;
            min-height: 100vh;
        }
        .header {
            background: linear-gradient(135deg, #1a1f36 0%, #0d1117 100%);
            border-bottom: 1px solid #21262d;
            padding: 1.5rem 2rem;
        }
        .header h1 {
            font-size: 1.5rem;
            background: linear-gradient(90deg, #58a6ff, #bc8cff);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
        }
        .header p { color: #8b949e; margin-top: 0.25rem; font-size: 0.9rem; }
        .container { max-width: 1200px; margin: 0 auto; padding: 2rem; }
        .input-section {
            background: #161b22;
            border: 1px solid #21262d;
            border-radius: 12px;
            padding: 1.5rem;
            margin-bottom: 2rem;
        }
        .input-section label {
            display: block; font-weight: 600; margin-bottom: 0.5rem;
            color: #c9d1d9;
        }
        textarea {
            width: 100%; height: 180px; padding: 1rem;
            background: #0d1117; border: 1px solid #30363d;
            border-radius: 8px; color: #e1e4e8; font-size: 0.9rem;
            resize: vertical; font-family: inherit;
        }
        textarea:focus { outline: none; border-color: #58a6ff; }

        /* File upload area */
        .upload-area {
            border: 2px dashed #30363d;
            border-radius: 10px;
            padding: 2rem;
            text-align: center;
            cursor: pointer;
            transition: all 0.3s;
            margin-bottom: 1rem;
            background: #0d1117;
        }
        .upload-area:hover, .upload-area.dragover {
            border-color: #58a6ff;
            background: rgba(88, 166, 255, 0.05);
        }
        .upload-area.has-file {
            border-color: #238636;
            background: rgba(35, 134, 54, 0.08);
        }
        .upload-area .icon { font-size: 2rem; margin-bottom: 0.5rem; }
        .upload-area .text { color: #8b949e; font-size: 0.9rem; }
        .upload-area .filename {
            color: #58a6ff; font-weight: 600; font-size: 1rem;
            margin-top: 0.5rem;
        }
        .upload-area input[type="file"] { display: none; }

        .btn {
            display: inline-block; padding: 0.75rem 2rem;
            background: linear-gradient(135deg, #238636, #2ea043);
            color: #fff; border: none; border-radius: 8px;
            font-size: 1rem; font-weight: 600; cursor: pointer;
            margin-top: 1rem; transition: all 0.2s;
        }
        .btn:hover { transform: translateY(-1px); box-shadow: 0 4px 12px rgba(35,134,54,0.4); }
        .btn:disabled { opacity: 0.5; cursor: not-allowed; transform: none; }
        .stats {
            display: grid; grid-template-columns: repeat(auto-fit, minmax(160px, 1fr));
            gap: 1rem; margin-bottom: 2rem;
        }
        .stat-card {
            background: #161b22; border: 1px solid #21262d;
            border-radius: 10px; padding: 1rem; text-align: center;
        }
        .stat-card .value {
            font-size: 1.8rem; font-weight: 700;
            background: linear-gradient(90deg, #58a6ff, #bc8cff);
            -webkit-background-clip: text; -webkit-text-fill-color: transparent;
        }
        .stat-card .label { color: #8b949e; font-size: 0.8rem; margin-top: 0.25rem; }
        .results-table {
            width: 100%; border-collapse: collapse;
            background: #161b22; border-radius: 12px; overflow: hidden;
            border: 1px solid #21262d;
        }
        .results-table th {
            background: #1c2128; color: #c9d1d9; padding: 0.75rem 1rem;
            text-align: left; font-size: 0.8rem; text-transform: uppercase;
            letter-spacing: 0.05em;
        }
        .results-table td {
            padding: 0.75rem 1rem; border-top: 1px solid #21262d;
            font-size: 0.85rem;
        }
        .results-table tr:hover { background: #1c2128; }
        .score-badge {
            display: inline-block; padding: 0.2rem 0.6rem;
            border-radius: 12px; font-weight: 600; font-size: 0.8rem;
        }
        .score-high { background: rgba(35,134,54,0.2); color: #3fb950; }
        .score-mid { background: rgba(187,128,9,0.2); color: #d29922; }
        .score-low { background: rgba(218,54,51,0.2); color: #f85149; }
        .spinner { display: none; margin-left: 0.5rem; }
        .spinner.active { display: inline-block; animation: spin 1s linear infinite; }
        @keyframes spin { to { transform: rotate(360deg); } }
        .reasoning { color: #8b949e; font-size: 0.8rem; max-width: 400px; }
        #results { display: none; }
        .toast-msg {
            border-radius: 8px; padding: 1rem;
            margin-top: 1rem; display: none;
            font-weight: 500;
        }
        .toast-msg.error {
            background: rgba(218,54,51,0.15); border: 1px solid #f85149; color: #f85149;
        }
        .toast-msg.success {
            background: rgba(35,134,54,0.15); border: 1px solid #3fb950; color: #3fb950;
        }
        .form-row {
            display: grid; grid-template-columns: 1fr 1fr; gap: 1.5rem;
            margin-bottom: 1rem;
        }
        @media (max-width: 768px) { .form-row { grid-template-columns: 1fr; } }
    </style>
</head>
<body>
    <div class="header">
        <h1>TalentMind AI</h1>
        <p>Intelligent Candidate Ranking Pipeline &mdash; Upload JSON, rank candidates</p>
    </div>
    <div class="container">
        <div class="input-section">
            <div class="form-row">
                <div>
                    <label>Upload Candidates (.json)</label>
                    <div class="upload-area" id="uploadArea" onclick="document.getElementById('fileInput').click()">
                        <div class="icon">+</div>
                        <div class="text">Click or drag &amp; drop a .json file</div>
                        <div class="filename" id="fileName"></div>
                        <input type="file" id="fileInput" accept=".json" onchange="handleFile(this)">
                    </div>
                </div>
                <div>
                    <label for="jd">Job Description</label>
                    <textarea id="jd">{{ default_jd }}</textarea>
                </div>
            </div>
            <button class="btn" id="rankBtn" onclick="runRanking()">
                Rank Candidates
                <span class="spinner" id="spinner">...</span>
            </button>
            <div class="toast-msg" id="toastMsg"></div>
        </div>

        <div id="results">
            <div class="stats" id="stats"></div>
            <table class="results-table">
                <thead>
                    <tr>
                        <th>#</th>
                        <th>Candidate</th>
                        <th>Title</th>
                        <th>Score</th>
                        <th>Semantic</th>
                        <th>Behavioral</th>
                        <th>Reasoning</th>
                    </tr>
                </thead>
                <tbody id="resultsBody"></tbody>
            </table>
        </div>
    </div>

    <script>
        let selectedFile = null;

        // Drag & drop
        const uploadArea = document.getElementById('uploadArea');
        uploadArea.addEventListener('dragover', (e) => { e.preventDefault(); uploadArea.classList.add('dragover'); });
        uploadArea.addEventListener('dragleave', () => uploadArea.classList.remove('dragover'));
        uploadArea.addEventListener('drop', (e) => {
            e.preventDefault();
            uploadArea.classList.remove('dragover');
            if (e.dataTransfer.files.length) {
                const file = e.dataTransfer.files[0];
                if (!file.name.endsWith('.json')) {
                    showToast('Only .json files are supported.', 'error');
                    return;
                }
                document.getElementById('fileInput').files = e.dataTransfer.files;
                handleFile(document.getElementById('fileInput'));
            }
        });

        function handleFile(input) {
            hideToast();
            if (input.files.length) {
                const file = input.files[0];
                if (!file.name.endsWith('.json') && !file.name.endsWith('.jsonl')) {
                    showToast('Only .json files are supported.', 'error');
                    selectedFile = null;
                    return;
                }
                selectedFile = file;
                document.getElementById('fileName').textContent = file.name + ' (' + formatSize(file.size) + ')';
                uploadArea.classList.add('has-file');
            }
        }

        function formatSize(bytes) {
            if (bytes < 1024) return bytes + ' B';
            if (bytes < 1048576) return (bytes / 1024).toFixed(1) + ' KB';
            return (bytes / 1048576).toFixed(1) + ' MB';
        }

        function showToast(msg, type) {
            const el = document.getElementById('toastMsg');
            el.textContent = msg;
            el.className = 'toast-msg ' + type;
            el.style.display = 'block';
        }

        function hideToast() {
            const el = document.getElementById('toastMsg');
            el.style.display = 'none';
        }

        async function runRanking() {
            const jd = document.getElementById('jd').value;
            const btn = document.getElementById('rankBtn');
            const spinner = document.getElementById('spinner');

            hideToast();

            if (!selectedFile) {
                showToast('Please upload a .json file with candidate records first.', 'error');
                return;
            }

            btn.disabled = true;
            spinner.classList.add('active');

            try {
                const formData = new FormData();
                formData.append('file', selectedFile);
                formData.append('jd', jd);

                const resp = await fetch('/api/rank', {
                    method: 'POST',
                    body: formData
                });

                // Guard against non-JSON responses (Flask HTML error pages)
                const contentType = resp.headers.get('content-type') || '';
                if (!contentType.includes('application/json')) {
                    const text = await resp.text();
                    throw new Error('Server error (HTTP ' + resp.status + '). Check the terminal for details.');
                }

                const data = await resp.json();

                if (!resp.ok) {
                    showToast(data.error || 'Server error', 'error');
                    return;
                }

                showToast('Loaded ' + data.total_loaded + ' candidates. Ranked top ' + data.ranked_count + '.', 'success');
                displayResults(data);
            } catch (e) {
                showToast('Error: ' + e.message, 'error');
            } finally {
                btn.disabled = false;
                spinner.classList.remove('active');
            }
        }

        function displayResults(data) {
            document.getElementById('results').style.display = 'block';

            const stats = document.getElementById('stats');
            stats.innerHTML = `
                <div class="stat-card"><div class="value">${data.total_loaded}</div><div class="label">Candidates Loaded</div></div>
                <div class="stat-card"><div class="value">${data.honeypots_flagged}</div><div class="label">Honeypots Flagged</div></div>
                <div class="stat-card"><div class="value">${data.survivors}</div><div class="label">Pre-filter Survivors</div></div>
                <div class="stat-card"><div class="value">${data.ranked_count}</div><div class="label">Ranked</div></div>
                <div class="stat-card"><div class="value">${data.elapsed_ms}ms</div><div class="label">Pipeline Time</div></div>
            `;

            const tbody = document.getElementById('resultsBody');
            tbody.innerHTML = '';
            data.ranked.forEach(c => {
                const scoreClass = c.score >= 0.75 ? 'score-high' : c.score >= 0.55 ? 'score-mid' : 'score-low';
                const row = document.createElement('tr');
                row.innerHTML = `
                    <td>${c.rank}</td>
                    <td><strong>${c.name || c.candidate_id}</strong></td>
                    <td>${c.current_title}</td>
                    <td><span class="score-badge ${scoreClass}">${c.score.toFixed(4)}</span></td>
                    <td>${c.semantic_score.toFixed(4)}</td>
                    <td>${c.behavioral_score.toFixed(4)}</td>
                    <td class="reasoning">${c.reasoning}</td>
                `;
                tbody.appendChild(row);
            });
        }
    </script>
</body>
</html>
"""


# ──────────────────────────────────────────────────────────────────────
# Pipeline runner (shared logic)
# ──────────────────────────────────────────────────────────────────────

def run_pipeline(
    raw_candidates: List[Dict[str, Any]],
    jd_text: str,
    top_n: int = 50,
) -> Dict[str, Any]:
    """Run the full ranking pipeline and return a result dict."""
    t0 = time.time()

    jd_profile = parse_job_description(jd_text)

    candidates = []
    for raw in raw_candidates:
        cand = normalize_candidate(raw)
        flagged, reason = is_honeypot(cand)
        cand["is_honeypot"] = flagged
        cand["honeypot_reason"] = reason
        candidates.append(cand)

    honeypots = sum(1 for c in candidates if c["is_honeypot"])
    definite, possible, disqualified = prefilter_candidates(candidates, jd_profile)
    survivors = definite + possible
    if not survivors:
        survivors = [c for c in candidates if not c.get("is_honeypot", False)]

    tfidf = build_tfidf_scorer(jd_profile, survivors)
    ranked = aggregate_and_rank(survivors, jd_profile, tfidf, top_n=top_n)

    elapsed = int((time.time() - t0) * 1000)

    result_list = []
    for entry in ranked:
        result_list.append({
            "rank": entry.get("rank"),
            "candidate_id": entry.get("candidate_id"),
            "name": entry.get("name", ""),
            "current_title": entry.get("current_title", ""),
            "score": entry.get("_score", 0),
            "semantic_score": entry.get("semantic_score", 0),
            "behavioral_score": entry.get("behavioral_score", 0),
            "reasoning": entry.get("reasoning", ""),
        })

    return make_serializable({
        "total_loaded": len(candidates),
        "honeypots_flagged": honeypots,
        "survivors": len(survivors),
        "ranked_count": len(ranked),
        "elapsed_ms": elapsed,
        "ranked": result_list,
    })


# ──────────────────────────────────────────────────────────────────────
# Routes
# ──────────────────────────────────────────────────────────────────────

@app.route("/")
def index():
    return render_template_string(HTML_TEMPLATE, default_jd=DEFAULT_JD.strip())


@app.route("/api/rank", methods=["POST"])
def api_rank():
    # ── Get uploaded file ────────────────────────────────────────────
    if "file" not in request.files:
        return jsonify({"error": "No file uploaded. Please upload a .json file."}), 400

    file = request.files["file"]
    if not file or file.filename == "":
        return jsonify({"error": "Empty file. Please select a valid .json file."}), 400

    # ── Validate file extension ──────────────────────────────────────
    filename = file.filename
    ext = Path(filename).suffix.lower()
    if ext not in ALLOWED_EXTENSIONS:
        return jsonify({
            "error": "Only .json files are supported."
        }), 400

    jd_text = request.form.get("jd", DEFAULT_JD)

    # ── Save uploaded file ───────────────────────────────────────────
    upload_path = UPLOAD_DIR / filename
    file.save(str(upload_path))

    # ── Parse the file using the unified loader ──────────────────────
    try:
        raw_candidates, skipped = load_candidates_file(str(upload_path))
    except json.JSONDecodeError as e:
        return jsonify({
            "error": f"Invalid JSON: {e.msg} at line {e.lineno}, column {e.colno}"
        }), 400
    except UnicodeDecodeError:
        return jsonify({"error": "File encoding error. Please upload a UTF-8 encoded file."}), 400
    except Exception as e:
        return jsonify({"error": f"Failed to parse file: {e}"}), 400

    if not raw_candidates:
        return jsonify({
            "error": (
                "No valid candidates found. File must be a JSON array of "
                "candidate objects, each with candidate_id and profile fields."
            )
        }), 400

    # ── Run pipeline ─────────────────────────────────────────────────
    try:
        result = run_pipeline(raw_candidates, jd_text, top_n=100)
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({"error": f"Pipeline error: {e}"}), 500

    # Add skipped count to the response for transparency
    result["skipped_records"] = skipped

    return jsonify(result)


if __name__ == "__main__":
    print("TalentMind AI Demo Server starting...")
    print("   Open http://localhost:5000 in your browser")
    print("   Upload a .json file with candidate records to rank them.")
    app.run(debug=True, port=5000)

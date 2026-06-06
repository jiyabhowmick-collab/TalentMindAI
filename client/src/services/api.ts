/**
 * services/api.ts — Centralised API communication layer.
 * All requests go to the Express backend (NEXT_PUBLIC_API_URL).
 * Uses credentials: "include" for HTTP-only cookie auth.
 */

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:4000";

/* ------------------------------------------------------------------ */
/*  Types                                                              */
/* ------------------------------------------------------------------ */

export interface AuthUser {
  _id: string;
  name: string;
  email: string;
}

export interface CandidateResult {
  _rank: number;
  _score: number;
  _semantic_score: number;
  _behavioral_score: number;
  _reasoning: string;
  name?: string;
  candidate_id?: string;
  current_title?: string;
  years_experience?: number;
  [key: string]: unknown;
}

export interface ResultsResponse {
  job_id: string;
  created_at?: string;
  total_candidates: number;
  returned: number;
  results: CandidateResult[];
}

/** 0=uploading  1=processing  2=ranking  3=done */
export type RankStep = 0 | 1 | 2 | 3;

/* ------------------------------------------------------------------ */
/*  Auth                                                               */
/* ------------------------------------------------------------------ */

export async function register(
  name: string,
  email: string,
  password: string,
): Promise<{ success: boolean; token: string; user: AuthUser }> {
  const res = await fetch(`${API_BASE}/api/auth/register`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    credentials: "include",
    body: JSON.stringify({ name, email, password }),
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({ error: "Registration failed" }));
    throw new Error(err.error || `Registration failed (${res.status})`);
  }
  const data = await res.json();
  if (data.token) localStorage.setItem("token", data.token);
  return data;
}

export async function login(
  email: string,
  password: string,
): Promise<{ success: boolean; token: string; user: AuthUser }> {
  const res = await fetch(`${API_BASE}/api/auth/login`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    credentials: "include",
    body: JSON.stringify({ email, password }),
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({ error: "Login failed" }));
    throw new Error(err.error || `Login failed (${res.status})`);
  }
  const data = await res.json();
  if (data.token) localStorage.setItem("token", data.token);
  return data;
}

export async function logout(): Promise<void> {
  await fetch(`${API_BASE}/api/auth/logout`, {
    method: "POST",
    credentials: "include",
  });
}

export async function refreshToken(): Promise<void> {
  const res = await fetch(`${API_BASE}/api/auth/refresh`, {
    method: "POST",
    credentials: "include",
  });
  if (!res.ok) throw new Error("Session expired. Please log in again.");
}

export async function getMe(): Promise<{ user: AuthUser }> {
  const res = await fetch(`${API_BASE}/api/auth/me`, { credentials: "include" });
  if (!res.ok) throw new Error("Not authenticated");
  return res.json();
}

/* ------------------------------------------------------------------ */
/*  Auth-aware fetch helper                                            */
/* ------------------------------------------------------------------ */

async function authFetch(url: string, options: RequestInit = {}): Promise<Response> {
  const opts: RequestInit = { ...options, credentials: "include" };
  let res = await fetch(url, opts);
  if (res.status === 401) {
    try {
      await refreshToken();
      res = await fetch(url, opts);
    } catch {
      throw new Error("Session expired. Please log in again.");
    }
  }
  return res;
}

/* ------------------------------------------------------------------ */
/*  PART 2 — Upload + rank with step callbacks                         */
/* ------------------------------------------------------------------ */

export interface UploadAndRankCallbacks {
  /** Called each time the step index advances (0→1→2→3) */
  onStepChange: (step: RankStep) => void;
  /** Called with total_candidates as soon as upload returns */
  onTotalCandidates: (total: number) => void;
  /** Called with the full results array when ranking is done */
  onComplete: (results: CandidateResult[], total: number, jobId: string) => void;
  /** Called on any unrecoverable error */
  onError: (message: string) => void;
}

/**
 * Full upload-and-rank flow wired to RankStep callbacks.
 * Advances steps in sync with real backend responses:
 *
 *  Frontend RankStep │ Backend /status step │ What it means
 *  ──────────────────┼──────────────────────┼──────────────────────────
 *  0  Uploading      │ (before POST returns) │ File being sent to server
 *  1  Processing     │ 1–2 (parse+normalise) │ Server processing file
 *  2  Ranking        │ 3–4 (tfidf+rank)      │ AI ranking in progress
 *  3  Done           │ 5 / results exist     │ Results ready
 */
export async function uploadAndRank(
  file: File,
  jobDescription: string,
  callbacks: UploadAndRankCallbacks,
): Promise<void> {
  const { onStepChange, onTotalCandidates, onComplete, onError } = callbacks;

  try {
    // ── Step 0: uploading (file transfer) ────────────────────────────
    onStepChange(0);

    const form = new FormData();
    form.append("file", file);
    form.append("job_description", jobDescription);

    const uploadRes = await authFetch(`${API_BASE}/api/upload`, {
      method: "POST",
      body:   form,
    });
    if (!uploadRes.ok) {
      const err = await uploadRes.json().catch(() => ({ error: "Upload failed" }));
      throw new Error(err.error || `Upload failed (${uploadRes.status})`);
    }
    const { job_id } = await uploadRes.json();
    // job_id returned immediately; pipeline running in Flask background thread

    // ── Steps 1 + 2: poll /status until backend reaches step 5 ──────
    const MAX_STATUS_POLLS = 360; // 12 min at 2 s intervals
    let lastFrontendStep: RankStep = 1;
    onStepChange(1); // server has the file — show "Processing"

    for (let attempt = 0; attempt < MAX_STATUS_POLLS; attempt++) {
      await sleep(2000);

      let statusData: {
        step: number;
        message: string;
        total: number;
        done: boolean;
        error?: string;
      };

      try {
        const statusRes = await authFetch(`${API_BASE}/api/status/${job_id}`);
        if (!statusRes.ok) continue; // transient error — retry
        statusData = await statusRes.json();
      } catch {
        continue; // network blip — retry
      }

      // Surface backend error
      if (statusData.step === -1) {
        throw new Error(statusData.message || "Pipeline error on server");
      }

      // Update total candidates as soon as it's known
      if (statusData.total > 0) {
        onTotalCandidates(statusData.total);
      }

      // Map backend step → frontend RankStep
      // backend 1–2 = Processing, backend 3–4 = Ranking, backend 5 = Done
      const frontendStep: RankStep =
        statusData.step <= 2 ? 1 :
        statusData.step <= 4 ? 2 : 3;

      if (frontendStep > lastFrontendStep) {
        lastFrontendStep = frontendStep;
        onStepChange(frontendStep);
      }

      // Job complete — fetch results
      if (statusData.done || statusData.step >= 5) {
        onStepChange(3);

        const resultsRes = await authFetch(`${API_BASE}/api/results/${job_id}`);
        if (!resultsRes.ok) {
          throw new Error(`Failed to fetch results (${resultsRes.status})`);
        }
        const data: ResultsResponse = await resultsRes.json();
        onComplete(data.results ?? [], data.total_candidates ?? statusData.total ?? 0, job_id);
        return;
      }
    }

    throw new Error("Ranking timed out after 12 minutes.");
  } catch (err: unknown) {
    onError(err instanceof Error ? err.message : "An unexpected error occurred.");
  }
}

/* ------------------------------------------------------------------ */
/*  Export CSV                                                         */
/* ------------------------------------------------------------------ */

export async function exportCSV(jobId: string, tier: 10 | 50 | 100): Promise<void> {
  const res = await authFetch(`${API_BASE}/api/export/${jobId}/${tier}`);
  if (!res.ok) {
    const err = await res.json().catch(() => ({ error: "Export failed" }));
    throw new Error(err.error || `Export failed (${res.status})`);
  }
  const blob = await res.blob();
  const url = URL.createObjectURL(blob);
  const anchor = document.createElement("a");
  anchor.href = url;
  anchor.download = `talent-mind_top-${tier}_${jobId.slice(0, 8)}.csv`;
  document.body.appendChild(anchor);
  anchor.click();
  anchor.remove();
  URL.revokeObjectURL(url);
}

/* ------------------------------------------------------------------ */
/*  Helpers                                                            */
/* ------------------------------------------------------------------ */

function sleep(ms: number) {
  return new Promise<void>((resolve) => setTimeout(resolve, ms));
}

/**
 * services/api.ts
 *
 * Centralised API communication layer.
 * All requests go to the Express backend (from NEXT_PUBLIC_API_URL).
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

export interface UploadResponse {
  job_id: string;
  total_candidates: number;
  returned: number;
  message: string;
}

export interface CandidateResult {
  _rank: number;
  _score: number;
  _semantic_score: number;
  _behavioral_score: number;
  _reasoning: string;
  name?: string;
  title?: string;
  [key: string]: unknown;
}

export interface ResultsResponse {
  job_id: string;
  created_at: string;
  total_candidates: number;
  returned: number;
  results: CandidateResult[];
}

export type ProgressStatus =
  | "uploading"
  | "processing"
  | "ranking"
  | "done"
  | "error";

/* ------------------------------------------------------------------ */
/*  Auth functions                                                     */
/* ------------------------------------------------------------------ */

export async function register(
  name: string,
  email: string,
  password: string
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
  password: string
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

  if (!res.ok) {
    throw new Error("Session expired. Please log in again.");
  }
}

export async function getMe(): Promise<{ user: AuthUser }> {
  const res = await fetch(`${API_BASE}/api/auth/me`, {
    credentials: "include",
  });

  if (!res.ok) {
    throw new Error("Not authenticated");
  }

  return res.json();
}

/* ------------------------------------------------------------------ */
/*  Data functions                                                     */
/* ------------------------------------------------------------------ */

/**
 * Wrapper around fetch that auto-retries once with a token refresh
 * if the first attempt returns 401.
 */
async function authFetch(url: string, options: RequestInit = {}): Promise<Response> {
  const opts: RequestInit = { ...options, credentials: "include" };

  let res = await fetch(url, opts);

  if (res.status === 401) {
    // Try refreshing the token
    try {
      await refreshToken();
      res = await fetch(url, opts);
    } catch {
      throw new Error("Session expired. Please log in again.");
    }
  }

  return res;
}

export async function uploadCandidates(
  file: File,
  jobDescription: string
): Promise<UploadResponse> {
  const form = new FormData();
  form.append("file", file);
  form.append("job_description", jobDescription);

  const res = await authFetch(`${API_BASE}/api/upload`, {
    method: "POST",
    body: form,
  });

  if (!res.ok) {
    const err = await res.json().catch(() => ({ error: "Upload failed" }));
    throw new Error(err.error || `Upload failed (${res.status})`);
  }

  return res.json();
}

export async function pollResults(
  jobId: string,
  onProgress: (status: ProgressStatus, data?: ResultsResponse) => void,
  intervalMs = 2000,
  maxAttempts = 150
): Promise<ResultsResponse> {
  onProgress("processing");

  for (let attempt = 0; attempt < maxAttempts; attempt++) {
    try {
      const res = await authFetch(`${API_BASE}/api/results/${jobId}`);

      if (res.status === 404) {
        onProgress("ranking");
        await sleep(intervalMs);
        continue;
      }

      if (!res.ok) {
        const err = await res.json().catch(() => ({ error: "Fetch failed" }));
        throw new Error(err.error || `Fetch failed (${res.status})`);
      }

      const data: ResultsResponse = await res.json();

      if (data.results && data.results.length > 0) {
        onProgress("done", data);
        return data;
      }

      onProgress("ranking");
      await sleep(intervalMs);
    } catch (err: any) {
      if (attempt > 5) {
        onProgress("error");
        throw err;
      }
      await sleep(intervalMs);
    }
  }

  onProgress("error");
  throw new Error("Polling timed out waiting for results.");
}

export async function exportCSV(
  jobId: string,
  tier: 10 | 50 | 100
): Promise<void> {
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
  return new Promise((resolve) => setTimeout(resolve, ms));
}

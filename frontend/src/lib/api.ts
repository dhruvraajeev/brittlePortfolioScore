// Typed client for the FastAPI backend. All paths are relative — the Vite
// dev server proxies /api/* to the Python service (see vite.config.ts).

export type Verdict = "resilient" | "moderate" | "fragile";

export interface Branch {
  score: number;
  weight: number;
  metrics: Record<string, number>;
}

export interface Spof {
  ticker: string;
  factor_exposure: number;
  exposure_share: number;
  shock: number;
  naive_loss: number;
  real_loss: number;
  amplification: number;
  per_ticker_exposure: Record<string, number>;
}

export interface Tail {
  annual_vol: number;
  max_drawdown: number;
  // 95% is the headline pair the UI shows; the 99% "really bad day" pair is
  // also returned by the backend for callers that want the deeper tail.
  var: number;
  cvar: number;
  var_99: number;
  cvar_99: number;
}

export interface Analysis {
  score: number;
  verdict: Verdict;
  branches: {
    position_sizing: Branch;
    co_movement: Branch;
    tail_risk: Branch;
  };
  sub_scores: Record<string, number>;
  branch_weights: Record<string, number>;
  weights: Record<string, number>;
  hidden_factor_pct: number;
  spof: Spof;
  tail: Tail;
  attribution: string;
  narrative: string;
}

export interface AnalyzeRequest {
  tickers: string[];
  weights?: Record<string, number>;
  period?: string;
  include_var?: boolean;
}

class ApiError extends Error {}

async function postJson<T>(path: string, body: unknown, signal?: AbortSignal): Promise<T> {
  const res = await fetch(path, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
    signal,
  });
  if (!res.ok) {
    let detail = `Request failed (${res.status})`;
    try {
      const data = await res.json();
      if (data?.detail) detail = data.detail;
    } catch {
      /* keep default */
    }
    throw new ApiError(detail);
  }
  return res.json() as Promise<T>;
}

export function analyze(req: AnalyzeRequest, signal?: AbortSignal): Promise<Analysis> {
  return postJson<Analysis>("/api/analyze", req, signal);
}

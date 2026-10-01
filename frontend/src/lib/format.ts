import type { Verdict } from "./api";

/** Verdict → its muted band color (CSS variable). */
export const verdictColor: Record<Verdict, string> = {
  resilient: "var(--ok)",
  moderate: "var(--warn)",
  fragile: "var(--bad)",
};

export const verdictLabel: Record<Verdict, string> = {
  resilient: "Resilient",
  moderate: "Moderate",
  fragile: "Fragile",
};

/** 0.263 → "26%" */
export function pct(x: number, digits = 0): string {
  return `${(x * 100).toFixed(digits)}%`;
}

/** A friendly label for each raw metric key. */
export const metricLabel: Record<string, string> = {
  correlation: "Correlation",
  hidden_factor: "Hidden factor",
  concentration: "Concentration",
  drawdown: "Drawdown",
  volatility: "Volatility",
  cvar: "Tail loss",
};

/** Normalize a weights map to shares that sum to 1. */
export function normalizedWeights(weights: Record<string, number>): Record<string, number> {
  const total = Object.values(weights).reduce((a, b) => a + b, 0) || 1;
  const out: Record<string, number> = {};
  for (const [k, v] of Object.entries(weights)) out[k] = v / total;
  return out;
}

/** Shared easing for every authored transition. */
export const EASE = [0.16, 1, 0.3, 1] as const;

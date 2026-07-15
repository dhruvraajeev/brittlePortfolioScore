import type { Verdict } from "./api";

/** Verdict → the light-blue-adjacent accent color for that band. */
export const verdictColor: Record<Verdict, string> = {
  resilient: "#4fe0b0",
  moderate: "#ffcf7a",
  fragile: "#ff7a90",
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
  cvar: "Tail risk",
};

/** Normalize a weights map to percentages that sum to 100. */
export function normalizedWeights(weights: Record<string, number>): Record<string, number> {
  const total = Object.values(weights).reduce((a, b) => a + b, 0) || 1;
  const out: Record<string, number> = {};
  for (const [k, v] of Object.entries(weights)) out[k] = v / total;
  return out;
}

"""
engine.score — combine the risk metrics into one 0-100 Fragility Score.

The combination is a two-level hierarchy, matching the three conceptual
branches of risk:

  Branch A — Position sizing     : concentration (HHI)
  Branch B — Co-movement / hidden: correlation + hidden factor (PCA)
  Branch C — Magnitude / tail    : drawdown + volatility + (optional) CVaR

Each branch is first collapsed into its own 0-100 score, then the three
branch scores are weighted into the final number. Doing it in two levels
(rather than one flat weighted sum of all six metrics) keeps the meaning
legible: the UI can show "your co-movement risk is 78/100" as a first-class
idea, and the branch weights answer the real design question — *how much
should each kind of risk matter* — without being tangled up in how many
metrics happen to sit inside each branch.

Every weight here is a judgment call, documented inline. Higher score =
more fragile, always in [0, 100].
"""

from __future__ import annotations

import pandas as pd

from .data import normalize_weights
from .metrics import (
    PCAResult,
    concentration_score,
    correlation_matrix,
    correlation_score,
    drawdown_score,
    hidden_factor_score,
    run_pca,
    volatility_score,
)
from .tail import tail_risk_score

# How much each branch matters in the final blend. Co-movement is weighted
# highest because it's the risk a ticker list *cannot* show you — the whole
# reason this tool exists (labels say "diversified," the math says "one
# bet"). Tail risk is next: it's real and visceral but partly visible to
# anyone who's watched their account in a bad month. Position sizing is
# weighted lowest because it's the most self-evident of the three — you can
# read concentration straight off your own weights.
BRANCH_WEIGHTS: dict[str, float] = {
    "position_sizing": 0.25,
    "co_movement": 0.45,
    "tail_risk": 0.30,
}

# Within co-movement, correlation and the hidden factor each get half:
# correlation is the pairwise view, the hidden factor the whole-portfolio
# view of the same underlying phenomenon, and both deserve equal say.
CO_MOVEMENT_WEIGHTS: dict[str, float] = {"correlation": 0.5, "hidden_factor": 0.5}

# Within tail risk, drawdown leads (it's the loss people actually remember
# living through), volatility next, and CVaR — when included — rounds it
# out with a statistical tail estimate. When CVaR is switched off, its
# weight is redistributed proportionally across the other two.
TAIL_WEIGHTS_WITH_VAR: dict[str, float] = {
    "drawdown": 0.40,
    "volatility": 0.35,
    "cvar": 0.25,
}
TAIL_WEIGHTS_NO_VAR: dict[str, float] = {"drawdown": 0.55, "volatility": 0.45}

for _w in (BRANCH_WEIGHTS, CO_MOVEMENT_WEIGHTS, TAIL_WEIGHTS_WITH_VAR, TAIL_WEIGHTS_NO_VAR):
    assert abs(sum(_w.values()) - 1.0) < 1e-9, "weight group must sum to 1.0"


def _verdict(score: float) -> str:
    """Map a 0-100 score to its band: 0-30 resilient, 31-60 moderate, 61+ fragile."""
    if score <= 30:
        return "resilient"
    if score <= 60:
        return "moderate"
    return "fragile"


def compute_branches(
    returns: pd.DataFrame,
    weights: dict[str, float],
    include_var: bool = True,
    pca: PCAResult | None = None,
    corr: pd.DataFrame | None = None,
) -> dict:
    """
    Compute all six metric scores and roll them up into the three branch
    scores. Returns a nested dict: each branch carries its own 0-100
    `score`, its `weight` in the final blend, and the individual `metrics`
    that produced it (so the UI can drill in).

    `pca` and `corr` accept precomputed results so the caller (analyze)
    can share one PCA fit and one correlation matrix across scoring and the
    single-point-of-failure attribution instead of recomputing them.
    """
    corr = correlation_matrix(returns) if corr is None else corr
    single_holding = returns.shape[1] < 2
    pca = pca if (pca is not None or single_holding) else run_pca(returns)

    # --- Branch A: position sizing -------------------------------------
    concentration = concentration_score(weights)
    branch_a = concentration  # a single metric IS the branch score

    # --- Branch B: co-movement / hidden risk ---------------------------
    correlation = correlation_score(returns, corr=corr)
    hidden_factor = hidden_factor_score(returns, pca=pca)
    branch_b = (
        correlation * CO_MOVEMENT_WEIGHTS["correlation"]
        + hidden_factor * CO_MOVEMENT_WEIGHTS["hidden_factor"]
    )

    # --- Branch C: magnitude / tail risk -------------------------------
    volatility = volatility_score(returns, weights)
    drawdown = drawdown_score(returns, weights)
    tail_metrics = {"volatility": volatility, "drawdown": drawdown}
    if include_var:
        cvar = tail_risk_score(returns, weights)
        tail_metrics["cvar"] = cvar
        tw = TAIL_WEIGHTS_WITH_VAR
        branch_c = drawdown * tw["drawdown"] + volatility * tw["volatility"] + cvar * tw["cvar"]
    else:
        tw = TAIL_WEIGHTS_NO_VAR
        branch_c = drawdown * tw["drawdown"] + volatility * tw["volatility"]

    return {
        "position_sizing": {
            "score": round(branch_a, 1),
            "weight": BRANCH_WEIGHTS["position_sizing"],
            "metrics": {"concentration": round(concentration, 1)},
        },
        "co_movement": {
            "score": round(branch_b, 1),
            "weight": BRANCH_WEIGHTS["co_movement"],
            "metrics": {
                "correlation": round(correlation, 1),
                "hidden_factor": round(hidden_factor, 1),
            },
        },
        "tail_risk": {
            "score": round(branch_c, 1),
            "weight": BRANCH_WEIGHTS["tail_risk"],
            "metrics": {k: round(v, 1) for k, v in tail_metrics.items()},
        },
    }


def sub_scores(
    returns: pd.DataFrame,
    weights: dict[str, float],
    include_var: bool = True,
    pca: PCAResult | None = None,
    corr: pd.DataFrame | None = None,
) -> dict[str, float]:
    """
    A flat {metric_name: 0-100} dict of every individual sub-score, across
    all three branches — the shape the radar chart wants. Split out from
    fragility_score() so callers (and tests) can get the individual numbers
    without the branch nesting.
    """
    weights = normalize_weights(weights)
    branches = compute_branches(returns, weights, include_var=include_var, pca=pca, corr=corr)
    flat: dict[str, float] = {}
    for branch in branches.values():
        flat.update(branch["metrics"])
    return flat


def fragility_score(
    returns: pd.DataFrame,
    weights: dict[str, float],
    include_var: bool = True,
    pca: PCAResult | None = None,
    corr: pd.DataFrame | None = None,
) -> dict:
    """
    The headline number plus the branch and metric breakdown behind it.

    `weights` is normalized here, once — every metric downstream assumes
    weights sum to 1.0, so this is the single place that guarantee is
    enforced rather than merely documented. A caller who already
    normalized pays nothing (dividing by a total of 1.0 is a no-op).

    Returns a plain dict, ready to be JSON-serialized straight to the
    frontend with no translation step.
    """
    weights = normalize_weights(weights)
    branches = compute_branches(returns, weights, include_var=include_var, pca=pca, corr=corr)

    total = sum(branches[name]["score"] * branches[name]["weight"] for name in branches)
    total = float(round(total, 1))

    # A flat view of every metric score, handy for the radar chart. Named
    # `flat_scores` to avoid shadowing the module-level sub_scores() function.
    flat_scores: dict[str, float] = {}
    for branch in branches.values():
        flat_scores.update(branch["metrics"])

    return {
        "score": total,
        "verdict": _verdict(total),
        "branches": branches,
        "sub_scores": flat_scores,
        "branch_weights": BRANCH_WEIGHTS,
    }

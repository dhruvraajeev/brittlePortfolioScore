"""
engine.tail — Value at Risk (VaR) and Conditional VaR (CVaR/Expected
Shortfall): the statistical "worst-case day" lens for Branch C.

VaR answers "on a normal-but-bad day, how much could I lose?" — the loss
threshold you only breach (1 - confidence) of the time. CVaR goes one step
further and answers "*when* I breach it, how bad is it on average?" — the
mean of the losses in that tail. CVaR is the more honest of the two,
because VaR says nothing about how far past the cliff you fall; that's why
CVaR is what feeds the tail-risk sub-score.

We use the *historical* method (read the losses straight off the actual
return history) rather than assuming a bell curve — real market returns
have fatter tails than a normal distribution, and the historical method
captures that for free without pretending we know the true distribution.

Two refinements over textbook historical simulation, both aimed at making
the tail estimate *more predictive of tomorrow* rather than merely a
faithful average of the past:

  1. Age weighting (Boudoukh–Richardson–Whitelaw, 1998). Naive historical
     simulation weights a calm day two years ago exactly like a violent day
     last week. But volatility clusters — recent behavior is far more
     informative about the near future. We assign each day an exponentially
     decaying weight (newest = heaviest) and read the quantile off the
     *weighted* empirical distribution. This keeps the fat tails of the
     historical method while letting the estimate respond to the current
     regime. With the decay set to 1.0 it collapses back to equal-weight
     historical simulation.

  2. Weighted Expected Shortfall. CVaR is the weight-averaged mean of the
     losses in the tail (each weighted by its age weight), not a plain mean
     of "days worse than VaR" — consistent with the same weighting that
     defines the VaR threshold.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

from .metrics import cap_and_scale, portfolio_returns

DEFAULT_CONFIDENCE = 0.95

# Exponential age-decay for historical simulation. 0.99/day gives a ~69-day
# half-life and an effective sample of ~1/(1-λ) ≈ 100 trading days: the most
# recent ~4-5 months dominate the tail estimate while older history still
# contributes, so the number tracks the current volatility regime without
# throwing away the fat-tail information in the longer record. Set to 1.0 for
# plain equal-weight historical simulation.
DEFAULT_DECAY = 0.99

# Below this many observations, age weighting concentrates almost all mass on
# a handful of recent days and the tail becomes pure noise — so we fall back
# to equal weighting, which at least uses every scarce data point evenly.
MIN_OBS_FOR_WEIGHTING = 60


def _age_weights(n: int, decay: float) -> np.ndarray:
    """
    Exponentially decaying weights over `n` chronologically ordered
    observations (row 0 oldest, row n-1 newest), normalized to sum to 1.

    The newest observation gets weight ∝ decay**0 = 1, the oldest
    decay**(n-1). A decay of 1.0 (or too small a sample) yields uniform
    weights — i.e. ordinary historical simulation.
    """
    if n <= 0:
        return np.array([])
    if decay >= 1.0 or n < MIN_OBS_FOR_WEIGHTING:
        return np.full(n, 1.0 / n)
    ages = np.arange(n - 1, -1, -1, dtype=float)  # oldest → newest = high → low age
    w = decay**ages
    return w / w.sum()


def _weighted_var_cvar(
    port_returns: pd.Series,
    confidence: float,
    decay: float,
) -> tuple[float, float]:
    """
    Age-weighted historical VaR and CVaR in one pass (they share the sort).

    Sort returns worst-first, walk the cumulative age weight until it
    reaches the tail probability (1 - confidence): the return sitting at
    that crossing is the VaR, and the weight-average of every return up to
    and including it is the CVaR. Both are negative daily returns (losses).
    """
    r = np.asarray(port_returns, dtype=float)
    n = r.size
    if n == 0:
        return 0.0, 0.0

    w = _age_weights(n, decay)

    order = np.argsort(r)  # ascending → worst losses first
    r_sorted = r[order]
    w_sorted = w[order]
    cum = np.cumsum(w_sorted)

    tail_p = 1.0 - confidence
    # First position where the cumulative weight reaches the tail mass; that
    # return is the VaR threshold. Clamp so a tiny sample still returns the
    # worst observed day rather than running off the end.
    idx = int(np.searchsorted(cum, tail_p, side="left"))
    idx = min(idx, n - 1)
    var = float(r_sorted[idx])

    tail_w = w_sorted[: idx + 1]
    tail_r = r_sorted[: idx + 1]
    total_w = float(tail_w.sum())
    cvar = float(np.dot(tail_r, tail_w) / total_w) if total_w > 0 else var

    return var, cvar


def historical_var(
    port_returns: pd.Series,
    confidence: float = DEFAULT_CONFIDENCE,
    decay: float = DEFAULT_DECAY,
) -> float:
    """
    Age-weighted historical VaR as a negative daily return. At 95%
    confidence this is the loss threshold such that only ~5% of the
    (age-weighted) distribution is worse — e.g. -0.021 == "on the worst 5%
    of days you lost more than 2.1%". Returned as a negative number.

    `decay` < 1.0 weights recent days more heavily (see DEFAULT_DECAY);
    `decay` == 1.0 gives ordinary equal-weight historical simulation.
    """
    var, _ = _weighted_var_cvar(port_returns, confidence, decay)
    return var


def historical_cvar(
    port_returns: pd.Series,
    confidence: float = DEFAULT_CONFIDENCE,
    decay: float = DEFAULT_DECAY,
) -> float:
    """
    Age-weighted historical CVaR / Expected Shortfall: the weight-average
    of the losses at or beyond the VaR threshold — the mean of the bad
    tail, not just its edge. Also a negative number, and always <= VaR (the
    average of the worst days can't be milder than the threshold that
    defines them).
    """
    _, cvar = _weighted_var_cvar(port_returns, confidence, decay)
    return cvar


def tail_risk_score(
    returns: pd.DataFrame,
    weights: dict[str, float],
    confidence: float = DEFAULT_CONFIDENCE,
    decay: float = DEFAULT_DECAY,
) -> float:
    """
    Map CVaR onto a 0-100 fragility score.

    Judgment call: we treat a CVaR of -6% (losing 6% on an average bad-tail
    day) as "as bad as it gets" for this score and scale linearly, clipping
    anything worse to 100. For context, a broad index portfolio's daily 95%
    CVaR sits around -2% to -3%; -6% is deep single-stock / leveraged
    territory. A calm portfolio near -2% scores ~33; a fragile one near -5%
    scores ~83.

    Because the underlying CVaR is now age-weighted, this sub-score reacts
    to a portfolio that has *recently* started taking violent tail losses,
    instead of waiting for two years of history to average the danger away.
    """
    CAP = 0.06  # a -6% daily CVaR maps to the maximum score of 100

    port = portfolio_returns(returns, weights)
    cvar = abs(historical_cvar(port, confidence, decay))
    return cap_and_scale(cvar, CAP)

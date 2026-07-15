"""
engine.stress — the hero feature: your single point of failure.

Two complementary readings of "which one holding hurts you most," both
grounded in the same portfolio:

  1. PCA attribution (the primary definition, per the spec): the dominant
     hidden factor is the first principal component of your holdings'
     movements. The holding most exposed to it — weighted by how much of
     it you actually own — is your single point of failure. This is an
     *interpretation of the PCA*: not "which stock is riskiest" but "which
     stock is your biggest bet on the one thing secretly moving everything."

  2. Correlation-aware shock (the narrative punch): if that holding fell by
     `shock` (default 30%), its correlated siblings slide with it, so the
     real portfolio damage is larger than the holding's own weight implies.
     The ratio of real damage to naive (weight-only) damage is the
     "amplification" — the "NVDA would hurt 3.4x more than its size
     suggests" line that makes the insight land.

Both are pure functions of a returns DataFrame and a normalized weights
dict — no I/O, no framework imports.
"""

from __future__ import annotations

from dataclasses import dataclass, field

import pandas as pd

from .metrics import PCAResult, correlation_matrix, daily_volatility, run_pca

DEFAULT_SHOCK = 0.30  # a 30% drop, expressed as a positive magnitude


@dataclass(frozen=True)
class SPOFResult:
    """
    The single-point-of-failure verdict plus the numbers behind it.

    Note the two exposure fields are in *different units*, easy to mix up:
    `factor_exposure` is the SPOF's raw |PC1 loading| (its own strength of
    tie to the hidden factor), while `exposure_share` / `per_ticker_exposure`
    are weight-normalized shares of the portfolio's *total* factor exposure
    that sum to 1 across holdings. Raw loading vs. share of the whole.
    """

    ticker: str  # the single point of failure
    factor_exposure: float  # its |PC1 loading|, 0..1 — raw exposure to the hidden factor
    exposure_share: float  # its share of the portfolio's total factor exposure, 0..1
    shock: float  # the drop size modeled, e.g. 0.30
    naive_loss: float  # weight-only portfolio loss if it drops `shock` (<= 0)
    real_loss: float  # correlation-aware portfolio loss (<= 0, usually worse)
    amplification: float  # real_loss / naive_loss — how much worse than it looks
    per_ticker_exposure: dict[str, float] = field(default_factory=dict)


def beta(corr: pd.DataFrame, vol: pd.Series, source: str, target: str) -> float:
    """
    How much `target` is expected to move for a 1-unit move in `source`:
    beta = corr(source, target) * vol[target] / vol[source].

    This is the CAPM beta written in correlation-first form. It equals the
    textbook cov(source, target) / var(source) because
    cov = corr * vol_source * vol_target, so dividing by var_source
    (= vol_source^2) leaves corr * vol_target / vol_source. A holding's
    beta on itself is corr(x, x) * vol_x / vol_x = 1.0, exactly as it
    should be: if it drops 30%, it dropped 30%.
    """
    return float(corr.loc[source, target] * vol[target] / vol[source])


def shock_loss(
    returns: pd.DataFrame,
    weights: dict[str, float],
    shocked: str,
    shock: float = DEFAULT_SHOCK,
    corr: pd.DataFrame | None = None,
) -> float:
    """
    The correlation-aware portfolio loss (a negative fraction) if
    `shocked` drops by `shock`. Every holding j is expected to move by
    -shock * beta(shocked, j); the portfolio loss is the weighted sum of
    those expected moves. Because a holding's beta on itself is 1, the
    shocked name contributes its own full -shock * weight, and every
    correlated sibling adds its share on top — which is exactly the drag
    a naive weight-only estimate misses.

    `corr` accepts a precomputed matrix so the full analysis can reuse the
    matrix it already needs for scoring.
    """
    vol = daily_volatility(returns)
    corr = correlation_matrix(returns) if corr is None else corr

    loss = 0.0
    for j in returns.columns:
        expected_move_j = -shock * beta(corr, vol, source=shocked, target=j)
        loss += weights[j] * expected_move_j
    return float(loss)


def naive_loss(weights: dict[str, float], shocked: str, shock: float = DEFAULT_SHOCK) -> float:
    """
    The naive, weight-only loss: "a `weight`-weighted holding dropping
    `shock` costs me weight * shock" — ignoring that correlated siblings
    fall too. This is the baseline the correlation-aware number beats.
    """
    return float(-shock * weights[shocked])


def single_point_of_failure(
    returns: pd.DataFrame,
    weights: dict[str, float],
    shock: float = DEFAULT_SHOCK,
    pca: PCAResult | None = None,
    corr: pd.DataFrame | None = None,
) -> SPOFResult:
    """
    Identify the single point of failure and quantify it.

    The SPOF is the holding maximizing weight * |PC1 loading| — the
    holding contributing most to the portfolio's exposure to the dominant
    hidden factor. (Using weight * exposure, not exposure alone, means a
    tiny 1% position that happens to be factor-heavy doesn't get flagged
    as your biggest vulnerability — your *actual* biggest bet on the
    hidden factor does.) We then quantify how badly a 30% drop in that
    holding would hit the whole portfolio once correlated siblings are
    dragged along, versus the naive weight-only estimate.

    `pca` and `corr` accept precomputed results so analyze() can share the
    same expensive intermediates used for scoring.
    """
    if returns.shape[1] < 2:
        # A single holding IS the whole portfolio: it's trivially its own
        # point of failure, fully exposed, and a 30% drop is exactly 30%
        # of its weight with nothing to amplify.
        only = returns.columns[0]
        return SPOFResult(
            ticker=only,
            factor_exposure=1.0,
            exposure_share=1.0,
            shock=shock,
            naive_loss=naive_loss(weights, only, shock),
            real_loss=naive_loss(weights, only, shock),
            amplification=1.0,
            per_ticker_exposure={only: 1.0},
        )

    pca = run_pca(returns) if pca is None else pca

    # |loading| is each holding's raw exposure to the dominant hidden
    # factor; multiply by weight to get its contribution to the
    # portfolio's factor exposure, then normalize into shares that sum to 1.
    abs_loadings = pca.pc1_loadings.abs()
    contribution = {t: float(weights[t] * abs_loadings[t]) for t in returns.columns}
    total = sum(contribution.values())
    exposure_share = {
        t: (c / total if total > 0 else 0.0) for t, c in contribution.items()
    }

    spof = max(exposure_share, key=exposure_share.get)

    real = shock_loss(returns, weights, spof, shock, corr=corr)
    naive = naive_loss(weights, spof, shock)
    # Guard the degenerate zero-weight case (naive == 0): fall back to the
    # neutral 1.0x (real == naive, no amplification) rather than dividing by
    # zero.
    amplification = float(real / naive) if naive != 0 else 1.0

    return SPOFResult(
        ticker=spof,
        factor_exposure=float(abs_loadings[spof]),
        exposure_share=float(exposure_share[spof]),
        shock=shock,
        naive_loss=naive,
        real_loss=real,
        amplification=amplification,
        per_ticker_exposure={t: float(v) for t, v in exposure_share.items()},
    )

"""
engine.analysis — the one call the API layer makes.

`analyze()` takes a returns DataFrame and a weights dict and returns the
complete, JSON-ready payload the frontend renders: the headline score, the
three branch scores, every sub-score, the single point of failure, the tail
metrics, the hidden-factor share, and a plain-English narrative. Everything
expensive (the PCA fit, the correlation matrix) is computed once here and
threaded through, so the whole analysis is a single pass over the data.
"""

from __future__ import annotations

import pandas as pd

from .data import normalize_weights
from .explain import attribution_sentence, template_narrative
from .metrics import (
    annualized_volatility,
    correlation_matrix,
    max_drawdown,
    portfolio_returns,
    run_pca,
)
from .score import fragility_score
from .stress import single_point_of_failure
from .tail import historical_cvar, historical_var


def analyze(
    returns: pd.DataFrame,
    weights: dict[str, float],
    include_var: bool = True,
) -> dict:
    """Full analysis of one portfolio — the single call the API layer makes."""
    weights = normalize_weights(weights)

    single_holding = returns.shape[1] < 2
    corr = correlation_matrix(returns)
    pca = None if single_holding else run_pca(returns)

    result = fragility_score(returns, weights, include_var=include_var, pca=pca, corr=corr)

    spof = single_point_of_failure(returns, weights, pca=pca, corr=corr)

    port = portfolio_returns(returns, weights)
    tail = {
        "annual_vol": annualized_volatility(port),
        "max_drawdown": max_drawdown(port),
        # 95% is the headline pair the UI shows; the 99% pair is the deeper
        # "really bad day" reading, exposed for callers that want it.
        "var": historical_var(port),
        "cvar": historical_cvar(port),
        "var_99": historical_var(port, confidence=0.99),
        "cvar_99": historical_cvar(port, confidence=0.99),
    }

    hidden_factor_pct = result["sub_scores"]["hidden_factor"] / 100.0

    analysis = {
        **result,  # score, verdict, branches, sub_scores, branch_weights
        "weights": weights,
        "hidden_factor_pct": hidden_factor_pct,
        "spof": {
            "ticker": spof.ticker,
            "factor_exposure": spof.factor_exposure,
            "exposure_share": spof.exposure_share,
            "shock": spof.shock,
            "naive_loss": spof.naive_loss,
            "real_loss": spof.real_loss,
            "amplification": spof.amplification,
            "per_ticker_exposure": spof.per_ticker_exposure,
        },
        "tail": tail,
    }

    analysis["attribution"] = attribution_sentence(analysis)
    analysis["narrative"] = template_narrative(analysis)

    return analysis

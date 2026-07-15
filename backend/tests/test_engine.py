"""
Sanity tests for the engine.

None of these touch the network — they build synthetic return series with a
known correlation structure so correctness can be checked against numbers we
fully control. If these pass, the math is right; whether real tickers behave
as expected is a separate, fuzzier question left to manual spot-checks
against real tickers.
"""

from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from engine.analysis import analyze
from engine.data import normalize_weights, to_returns
from engine.explain import attribution_sentence, template_narrative
from engine.metrics import (
    cap_and_scale,
    concentration_score,
    correlation_matrix,
    correlation_score,
    daily_volatility,
    drawdown_score,
    effective_n,
    herfindahl_index,
    hidden_factor_score,
    max_drawdown,
    portfolio_returns,
    run_pca,
    volatility_score,
)
from engine.score import BRANCH_WEIGHTS, fragility_score, sub_scores
from engine.stress import beta, naive_loss, shock_loss, single_point_of_failure
from engine.tail import historical_cvar, historical_var, tail_risk_score

N_DAYS = 500
SEED = 7


def _correlated_returns(n_tickers: int, rho: float, n_days: int = N_DAYS) -> pd.DataFrame:
    """
    Synthetic returns for `n_tickers` holdings whose pairwise correlation is
    approximately `rho`, via a single shared market factor plus independent
    per-ticker noise. Every column has ~equal volatility regardless of rho,
    so betas reduce to correlations — which makes the SPOF math easy to
    reason about by hand.
    """
    rng = np.random.default_rng(SEED)
    market = rng.normal(0, 0.01, n_days)
    tickers = [f"T{i}" for i in range(n_tickers)]
    data = {}
    for name in tickers:
        idio = rng.normal(0, 0.01, n_days)
        data[name] = rho * market + np.sqrt(max(0.0, 1 - rho**2)) * idio
    return pd.DataFrame(data)


def _even(returns: pd.DataFrame) -> dict[str, float]:
    return normalize_weights({t: 1.0 for t in returns.columns})


# ---------------------------------------------------------------------------
# Metrics
# ---------------------------------------------------------------------------


def test_correlation_score_tracks_correlation():
    assert correlation_score(_correlated_returns(5, 0.9)) > 70
    assert correlation_score(_correlated_returns(5, 0.0)) < 20


def test_correlation_score_zero_for_single_holding():
    assert correlation_score(_correlated_returns(1, 0.0)) == 0.0


def test_concentration_score():
    even = normalize_weights({t: 1.0 for t in "ABCDEFGHIJ"})
    assert herfindahl_index(even) == pytest.approx(0.1, abs=1e-9)
    assert effective_n(even) == pytest.approx(10.0, abs=1e-6)
    assert concentration_score(even) == pytest.approx(0.0, abs=1e-6)

    lopsided = normalize_weights({"BIG": 90, **{t: 10 / 9 for t in "BCDEFGHIJ"}})
    assert concentration_score(lopsided) > 80


def test_pca_and_hidden_factor():
    tight = _correlated_returns(5, 0.999)
    loose = _correlated_returns(5, 0.0)
    assert hidden_factor_score(tight) > 95
    assert hidden_factor_score(loose) < 40

    pca = run_pca(tight)
    # Explained-variance ratios sum to 1 and are sorted descending.
    assert pca.explained_variance.sum() == pytest.approx(1.0, abs=1e-6)
    assert pca.explained_variance[0] >= pca.explained_variance[-1]
    # One loading per ticker.
    assert set(pca.pc1_loadings.index) == set(tight.columns)


def test_max_drawdown():
    assert max_drawdown(pd.Series([0.01] * 100)) == pytest.approx(0.0, abs=1e-9)
    dropped = pd.Series([0.01] * 10 + [-0.20] + [0.0] * 10)
    assert max_drawdown(dropped) < -0.15


def test_portfolio_returns_is_weighted_average():
    returns = pd.DataFrame({"A": [0.10, -0.10], "B": [0.02, 0.02]})
    result = portfolio_returns(returns, {"A": 0.25, "B": 0.75})
    expected = pd.Series([0.25 * 0.10 + 0.75 * 0.02, 0.25 * -0.10 + 0.75 * 0.02])
    pd.testing.assert_series_equal(result, expected, check_names=False)


# ---------------------------------------------------------------------------
# Tail risk (VaR / CVaR)
# ---------------------------------------------------------------------------


def test_var_and_cvar_ordering():
    returns = _correlated_returns(4, 0.4)
    port = portfolio_returns(returns, _even(returns))
    var = historical_var(port)
    cvar = historical_cvar(port)
    # Both are losses, and CVaR (mean of the worst tail) is never milder
    # than VaR (the tail's edge).
    assert cvar <= var <= 0
    assert 0.0 <= tail_risk_score(returns, _even(returns)) <= 100.0


def test_age_weighting_reacts_to_recent_turbulence():
    """
    The whole point of age weighting: the same cluster of violent days
    should register as a worse tail when it's *recent* than when it's
    ancient. Build one calm series, then inject an identical burst of large
    losses either at the very start or the very end.
    """
    rng = np.random.default_rng(SEED)
    n = 400
    calm = rng.normal(0.0, 0.008, n)
    shock = np.full(10, -0.06)  # a 10-day crash

    recent = pd.Series(np.concatenate([calm, shock]))
    ancient = pd.Series(np.concatenate([shock, calm]))

    # Age-weighted CVaR: recent crash bites harder (more negative).
    assert historical_cvar(recent) < historical_cvar(ancient)

    # With decay switched off (equal weight), position no longer matters —
    # same days, same distribution, same number.
    assert historical_cvar(recent, decay=1.0) == pytest.approx(
        historical_cvar(ancient, decay=1.0)
    )


# ---------------------------------------------------------------------------
# Single point of failure (the hero)
# ---------------------------------------------------------------------------


def test_spof_amplifies_more_for_correlated_basket():
    tech = _correlated_returns(5, 0.85)
    diversified = _correlated_returns(5, 0.05)

    tech_spof = single_point_of_failure(tech, _even(tech))
    div_spof = single_point_of_failure(diversified, _even(diversified))

    # A crash propagates through correlation, so the correlation-aware loss
    # is worse than the naive weight-only loss...
    assert tech_spof.real_loss < tech_spof.naive_loss < 0
    # ...and it's amplified much more in the all-correlated basket. This is
    # the headline product claim ("3.4x worse than its weight").
    assert tech_spof.amplification > 2.5
    assert tech_spof.amplification > div_spof.amplification


def test_spof_shock_loss_beats_naive():
    returns = _correlated_returns(4, 0.7)
    weights = _even(returns)
    ticker = returns.columns[0]
    assert shock_loss(returns, weights, ticker) < naive_loss(weights, ticker) < 0


def test_spof_single_holding_is_itself():
    returns = _correlated_returns(1, 0.0)
    spof = single_point_of_failure(returns, _even(returns))
    assert spof.ticker == returns.columns[0]
    assert spof.amplification == 1.0


def test_spof_exposure_shares_sum_to_one():
    returns = _correlated_returns(6, 0.5)
    spof = single_point_of_failure(returns, _even(returns))
    assert sum(spof.per_ticker_exposure.values()) == pytest.approx(1.0, abs=1e-6)


# ---------------------------------------------------------------------------
# Score (branch combination)
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("rho", [0.0, 0.3, 0.6, 0.9])
def test_all_sub_scores_bounded(rho):
    returns = _correlated_returns(4, rho)
    for name, value in sub_scores(returns, _even(returns)).items():
        assert 0.0 <= value <= 100.0, f"{name}={value} out of range"


def test_fragility_score_is_weighted_branch_sum():
    returns = _correlated_returns(4, 0.5)
    result = fragility_score(returns, _even(returns))
    expected = sum(
        result["branches"][b]["score"] * BRANCH_WEIGHTS[b] for b in BRANCH_WEIGHTS
    )
    assert result["score"] == pytest.approx(round(expected, 1), abs=1e-6)
    assert 0.0 <= result["score"] <= 100.0


def test_fragility_ranks_correlated_above_diversified():
    tech = _correlated_returns(5, 0.85)
    diversified = _correlated_returns(5, 0.05)
    tech_score = fragility_score(tech, _even(tech))["score"]
    div_score = fragility_score(diversified, _even(diversified))["score"]
    assert tech_score > div_score + 15


def test_weights_are_normalized_internally():
    returns = _correlated_returns(3, 0.5)
    raw = fragility_score(returns, {"T0": 5000, "T1": 3000, "T2": 2000})
    pre = fragility_score(returns, {"T0": 0.5, "T1": 0.3, "T2": 0.2})
    assert raw["score"] == pre["score"]


# ---------------------------------------------------------------------------
# Full analysis payload
# ---------------------------------------------------------------------------


def test_analyze_payload_shape():
    returns = _correlated_returns(5, 0.6)
    a = analyze(returns, _even(returns))
    for key in (
        "score",
        "verdict",
        "branches",
        "sub_scores",
        "spof",
        "tail",
        "hidden_factor_pct",
        "attribution",
        "narrative",
    ):
        assert key in a, f"missing key: {key}"
    assert isinstance(a["narrative"], str) and len(a["narrative"]) > 0
    assert a["spof"]["ticker"] in returns.columns
    # The template narrative names the single point of failure.
    assert a["spof"]["ticker"] in a["narrative"]


def test_analyze_verdict_bands():
    resilient = analyze(_correlated_returns(6, 0.02), _even(_correlated_returns(6, 0.02)))
    assert resilient["verdict"] == "resilient"


# ---------------------------------------------------------------------------
# cap_and_scale — the shared "raw stat -> 0-100" primitive
# ---------------------------------------------------------------------------


def test_cap_and_scale_endpoints_and_clip():
    assert cap_and_scale(0.0, 0.6) == 0.0
    assert cap_and_scale(0.6, 0.6) == pytest.approx(100.0)
    assert cap_and_scale(0.3, 0.6) == pytest.approx(50.0)
    # At or past the cap saturates at exactly 100 rather than extrapolating.
    assert cap_and_scale(0.9, 0.6) == 100.0
    assert cap_and_scale(1000.0, 0.6) == 100.0
    # Negatives floor at 0 (a score reads as "how much danger," never below).
    assert cap_and_scale(-0.5, 0.6) == 0.0


def test_score_caps_saturate_at_100():
    # A drawdown deeper than the 60% cap clips to exactly 100.
    crash = pd.DataFrame({"X": [0.0] * 10 + [-0.70] + [0.0] * 10})
    assert drawdown_score(crash, {"X": 1.0}) == 100.0

    # Annualized vol well past the 50% cap clips to exactly 100.
    wild = pd.DataFrame({"X": [0.1, -0.1] * 100})
    assert volatility_score(wild, {"X": 1.0}) == 100.0

    # And a violent enough tail clips the CVaR sub-score to 100.
    assert tail_risk_score(wild, {"X": 1.0}) == 100.0


# ---------------------------------------------------------------------------
# Beta (the building block of the correlation-aware shock)
# ---------------------------------------------------------------------------


def test_beta_on_self_is_one():
    returns = _correlated_returns(4, 0.6)
    corr = correlation_matrix(returns)
    vol = daily_volatility(returns)
    for t in returns.columns:
        assert beta(corr, vol, source=t, target=t) == pytest.approx(1.0)


def test_beta_scales_with_target_volatility():
    # target moves exactly twice as much as source, perfectly in step:
    # corr = 1, vol_target / vol_source = 2  ->  beta = 2.
    returns = pd.DataFrame({"S": [0.01, -0.01, 0.02, -0.02], "T": [0.02, -0.02, 0.04, -0.04]})
    corr = correlation_matrix(returns)
    vol = daily_volatility(returns)
    assert beta(corr, vol, source="S", target="T") == pytest.approx(2.0)
    assert beta(corr, vol, source="T", target="S") == pytest.approx(0.5)


# ---------------------------------------------------------------------------
# data.py — the conversion and normalization guards
# ---------------------------------------------------------------------------


def test_to_returns_raises_on_no_overlap():
    # A single price row leaves nothing after pct_change().dropna().
    with pytest.raises(ValueError, match="overlapping"):
        to_returns(pd.DataFrame({"A": [100.0], "B": [50.0]}))


def test_normalize_weights_rejects_empty():
    with pytest.raises(ValueError):
        normalize_weights({})


def test_normalize_weights_rejects_nonpositive_total():
    with pytest.raises(ValueError, match="positive"):
        normalize_weights({"A": 0.0, "B": 0.0})


def test_normalize_weights_sums_to_one():
    out = normalize_weights({"A": 3.0, "B": 1.0})
    assert sum(out.values()) == pytest.approx(1.0)
    assert out["A"] == pytest.approx(0.75)


# ---------------------------------------------------------------------------
# explain.py — the deterministic sentences (wording, not just presence)
# ---------------------------------------------------------------------------


def test_attribution_sentence_names_spof_and_amplification():
    a = analyze(_correlated_returns(5, 0.8), _even(_correlated_returns(5, 0.8)))
    sentence = attribution_sentence(a)
    assert a["spof"]["ticker"] in sentence
    assert "single point of failure" in sentence
    # It quantifies the amplification with an "x worse" multiple.
    assert "worse than its weight" in sentence
    assert "x" in sentence


def test_template_narrative_states_score_and_verdict():
    a = analyze(_correlated_returns(5, 0.8), _even(_correlated_returns(5, 0.8)))
    narrative = template_narrative(a)
    assert f"{a['score']:.0f}/100" in narrative
    # The narrative ends with the attribution, so it also names the SPOF.
    assert a["spof"]["ticker"] in narrative

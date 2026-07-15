"""
metrics — the five sub-scores that feed the gauge and the radar chart.

Each "raw stat" function below computes a real, textbook quantity
(correlation, HHI, an eigenvalue share, a drawdown, a volatility) that
means something on its own. Each matching "*_score" function then maps
that raw stat onto a 0-100 "how fragile does this make you" scale.

That mapping step — where does 0 end and 100 begin — is a judgment call,
not a law of physics. Day1.html calls this out explicitly (see the
"weighted scoring" concept): there is no universally correct place to draw
the line between "calm" and "wild." The thresholds chosen here are
documented inline so they can be argued with and tuned, not treated as
ground truth.

Every *_score function is guaranteed to return a float in [0, 100], where
higher always means more fragile. That invariant is what score.py and the
sanity tests in tests/test_engine.py both rely on.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd

# Trading days in a year, used to annualize daily statistics. 252 is the
# standard convention (365 calendar days minus weekends and market
# holidays) — not exact, but the number everyone in finance uses so
# annualized figures are comparable across sources.
TRADING_DAYS_PER_YEAR = 252


def cap_and_scale(value: float, cap: float) -> float:
    """
    The shared shape behind every "raw stat -> 0-100 fragility" mapping.

    Clamp `value` to [0, cap] and stretch that onto [0, 100] linearly: 0 (or
    anything negative) scores 0, `cap` — the "as bad as it gets" judgment
    call each caller supplies — scores 100, and everything past `cap` is
    clipped to 100 rather than extrapolated (a score ranks "how fragile," it
    doesn't keep counting past "very"). Centralizing it here is what makes
    the module-level guarantee — every *_score returns a float in [0, 100] —
    true by construction instead of by four separate hand-written copies.
    """
    return float(min(max(value, 0.0) / cap, 1.0) * 100)


def _weights_series(returns: pd.DataFrame, weights: dict[str, float]) -> pd.Series:
    """
    Align a {ticker: weight} dict to the column order of a returns
    DataFrame and return it as a Series. Centralized here so every metric
    that needs "weights in the same order as the columns" gets it the same
    way, instead of five slightly different reindex calls.
    """
    missing = [t for t in weights if t not in returns.columns]
    if missing:
        raise ValueError(f"weights reference unknown tickers: {', '.join(missing)}")
    return pd.Series(weights).reindex(returns.columns).fillna(0.0)


def portfolio_returns(returns: pd.DataFrame, weights: dict[str, float]) -> pd.Series:
    """
    Collapse a DataFrame of per-ticker daily returns into a single daily
    return series for the *whole portfolio*: on each day, the weighted
    average of how much every holding moved.

    This is the series that drawdown and volatility are computed on — the
    "how did my actual account do" line, as opposed to any one holding's
    line.
    """
    w = _weights_series(returns, weights)
    return returns[w.index].mul(w, axis=1).sum(axis=1)


# ---------------------------------------------------------------------------
# 1. Correlation — "do my holdings move together?"
# ---------------------------------------------------------------------------


def correlation_matrix(returns: pd.DataFrame) -> pd.DataFrame:
    """
    The full pairwise Pearson correlation matrix of daily returns: one row
    and one column per ticker, each cell a number from -1 (always move
    opposite) to +1 (always move together).

    This single matrix is a "friendship map" of the portfolio — it's also
    the input to the hidden-factor (PCA) step below, so we compute it once
    here and hand it to whoever needs it, rather than recomputing.
    """
    return returns.corr()


def avg_pairwise_correlation(corr: pd.DataFrame) -> float:
    """
    Average correlation across every *distinct pair* of holdings — i.e.
    the off-diagonal cells of the correlation matrix, excluding the
    diagonal (which is trivially 1.0, a stock's correlation with itself,
    and would just water down the average toward "looks fine").

    A single holding has no pairs, so this returns 0.0 (nothing to be
    correlated with — not fragile by this particular measure).
    """
    n = corr.shape[0]
    if n < 2:
        return 0.0

    # Sum every cell, subtract the diagonal (n cells of exactly 1.0), then
    # divide by the number of off-diagonal cells to get the mean.
    off_diagonal_sum = corr.to_numpy().sum() - n
    off_diagonal_count = n * n - n
    return float(off_diagonal_sum / off_diagonal_count)


def correlation_score(returns: pd.DataFrame, corr: pd.DataFrame | None = None) -> float:
    """
    Map average pairwise correlation (a -1..+1 stat) onto a 0-100
    fragility score.

    Judgment call: correlations below 0 (holdings that genuinely hedge
    each other) are treated as equally "not fragile" as a correlation of
    0 — we don't reward negative correlation with a below-zero score,
    since a score is meant to read as "how much danger," not "how clever
    is this hedge." So we clip the input to [0, 1] before scaling, then
    stretch that onto [0, 100] linearly. An average correlation of 0.7
    (the kind of number a "diversified-by-name" tech-heavy basket
    routinely produces — e.g. AMZN/GOOGL/V/HD/MSFT, five names across four
    labeled sectors that still ride the same tide) lands at a 70 —
    solidly in the "fragile" band.

    `corr` lets a caller that already has the correlation matrix (e.g.
    score.sub_scores(), which also needs it for hidden_factor_score) pass
    it straight through instead of paying for `returns.corr()` a second
    time — real work for anything beyond a handful of tickers, since it's
    an O(tickers^2 * days) computation. Called on its own, as in the
    tests below, it computes the matrix itself exactly as before.
    """
    corr = correlation_matrix(returns) if corr is None else corr
    avg_corr = avg_pairwise_correlation(corr)
    return cap_and_scale(avg_corr, 1.0)


# ---------------------------------------------------------------------------
# 2. Concentration (HHI) — "how evenly is your money actually split?"
# ---------------------------------------------------------------------------


def herfindahl_index(weights: dict[str, float]) -> float:
    """
    The Herfindahl-Hirschman Index: square each holding's weight and sum
    them. Borrowed from antitrust economics, where regulators use it to
    flag an industry dominated by one company.

    Ranges from 1/N (perfectly even across N holdings) to 1.0 (100% in a
    single holding). Squaring is what makes it "blunt but sensitive to
    the big one" — a holding at 50% contributes 0.25 to the sum, four
    times as much as a holding at 25%, which is exactly the "the big
    position dominates" signal we want.
    """
    if not weights:
        raise ValueError("herfindahl_index needs at least one holding")
    return float(sum(w * w for w in weights.values()))


def effective_n(weights: dict[str, float]) -> float:
    """
    The reciprocal of HHI: "effective number of holdings." Ten positions
    where one is 90% of the money isn't ten real bets — this number says
    how many *even-sized* bets your actual split behaves like.

    A perfectly even 10-holding portfolio scores 10.0 here. A portfolio
    that's 90% one name and 10% split nine ways scores close to 1.1 — you
    "own" ten tickers but are effectively riding one.
    """
    hhi = herfindahl_index(weights)
    return float(1.0 / hhi) if hhi > 0 else 0.0


def concentration_score(weights: dict[str, float]) -> float:
    """
    Map "effective number of holdings" onto a 0-100 fragility score by
    comparing it to the *actual* number of holdings you own.

    Judgment call: fragility here is about the *gap* between how many
    tickers you hold and how many real bets that split behaves like —
    effective_n / n == 1.0 means your weights are perfectly even (as
    un-concentrated as that many holdings can be) -> score 0. As
    effective_n falls toward 1 (all the money effectively riding on one
    name, regardless of how many tickers are on the screen) -> score
    approaches 100. A single-holding portfolio is the degenerate case:
    effective_n == n == 1, ratio == 1.0, so it correctly scores 0 for
    concentration specifically — its fragility shows up in the other
    four sub-scores instead (no diversification benefit anywhere), not
    here.
    """
    n = len(weights)
    if n == 0:
        raise ValueError("concentration_score needs at least one holding")

    ratio = effective_n(weights) / n  # 1.0 = perfectly even, ->0 = one name dominates
    return float((1.0 - ratio) * 100)


# ---------------------------------------------------------------------------
# 3. Hidden factor (PCA) — "how much of this is secretly one bet?"
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class PCAResult:
    """
    The outcome of running PCA on the portfolio's return history. Bundled
    into one object because the two things a caller wants — "how dominant
    is the top hidden factor" (explained_variance) and "which holding is
    most exposed to it" (pc1_loadings) — come out of the *same* fit, and
    recomputing PCA twice to get them separately would be wasteful.

    explained_variance : share of total movement each principal component
        explains, largest first. explained_variance[0] is the headline
        "N% of everything is one hidden force" number.
    pc1_loadings : each ticker's coefficient on the first (dominant)
        component — how strongly that holding moves with the hidden
        factor. Indexed by ticker. Sign is mathematically arbitrary (a
        component and its negation are the same axis), so callers care
        about the *magnitude* of each loading, not its sign.
    """

    explained_variance: np.ndarray
    pc1_loadings: pd.Series


def run_pca(returns: pd.DataFrame) -> PCAResult:
    """
    Run PCA on *standardized* daily returns, which is mathematically the
    same as diagonalizing the correlation matrix (not the covariance
    matrix). Standardizing first — z-scoring each column to mean 0,
    variance 1 — is what makes this about how *alike the movements are*
    rather than about which stock happens to be the loudest: without it,
    a single high-volatility name would dominate the top component just
    by having big numbers, telling you nothing about shared risk.

    We compute it directly with a NumPy SVD rather than pulling in
    scikit-learn. PCA *is* the SVD of the centered (here, standardized)
    data matrix: the right-singular vectors are the components and the
    squared singular values are proportional to the variance each explains.
    This is exactly what scikit-learn's PCA does under the hood, so the
    numbers are identical — but it drops scikit-learn and its heavy SciPy
    dependency, which matters for a lean serverless deploy and for cold-start
    time. Downstream code only ever uses the *magnitude* of the loadings and
    the variance *ratios*, both of which are invariant to the arbitrary sign
    a singular vector can carry.

    Because the input is standardized, explained_variance[0] equals the
    largest eigenvalue of the correlation matrix divided by the number of
    holdings — i.e. exactly the "hidden factor share" definition.
    """
    if returns.shape[1] < 2:
        raise ValueError("PCA needs at least two holdings")

    x = returns.to_numpy(dtype=float)
    mean = x.mean(axis=0)
    # ddof=0 (population std) to match the standard StandardScaler
    # convention; the choice is irrelevant to the variance *ratios* anyway.
    std = x.std(axis=0, ddof=0)
    std[std == 0] = 1.0  # a perfectly flat column has no variance to scale
    standardized = (x - mean) / std

    # Economy SVD of the standardized matrix. singular_values**2 are the
    # (unnormalized) explained variances; components are the rows of Vt.
    _, singular_values, vt = np.linalg.svd(standardized, full_matrices=False)
    variances = singular_values**2
    explained = variances / variances.sum()

    return PCAResult(
        explained_variance=explained,
        pc1_loadings=pd.Series(vt[0], index=returns.columns),
    )


def hidden_factor_share(returns: pd.DataFrame, pca: PCAResult | None = None) -> float:
    """
    What fraction of your holdings' combined day-to-day wiggle is
    explained by a single dominant, invisible force? This is the share of
    total variance carried by the first principal component — e.g. "72% of
    everything that happens to this portfolio is really one force."

    A single holding is trivially "100% one factor" (there's only one
    thing that can move), which is the correct, if degenerate, answer.

    `pca` accepts a precomputed PCAResult so a caller that already ran PCA
    (e.g. for the single-point-of-failure attribution) doesn't pay to fit
    it twice. Defaults to computing it here when called standalone.
    """
    if returns.shape[1] < 2:
        return 1.0

    pca = run_pca(returns) if pca is None else pca
    return float(pca.explained_variance[0])


def hidden_factor_score(returns: pd.DataFrame, pca: PCAResult | None = None) -> float:
    """
    Map the hidden-factor share (already a natural 0..1 fraction) onto a
    0-100 fragility score. No further judgment call needed here beyond
    the ones already made in hidden_factor_share() — this is the one
    sub-score where the raw stat *is* the intuitive percentage a person
    would want to see ("72% one bet" -> a 72).
    """
    share = hidden_factor_share(returns, pca)
    return cap_and_scale(share, 1.0)


# ---------------------------------------------------------------------------
# 4. Drawdown — "how deep would this have dragged you under?"
# ---------------------------------------------------------------------------


def max_drawdown(portfolio_daily_returns: pd.Series) -> float:
    """
    The largest peak-to-valley decline in the portfolio's cumulative
    value over the period, as a negative fraction (e.g. -0.33 for a 33%
    drawdown).

    We build a cumulative wealth curve from the daily returns (start at
    1.0, compound each day's return), track the running peak of that
    curve, and measure how far below that peak the curve ever falls. This
    is the "underwater curve" view of drawdown — the deepest point of it
    is the max drawdown.
    """
    wealth = (1.0 + portfolio_daily_returns).cumprod()
    running_peak = wealth.cummax()
    drawdown = wealth / running_peak - 1.0  # always <= 0
    return float(drawdown.min())


def drawdown_score(returns: pd.DataFrame, weights: dict[str, float]) -> float:
    """
    Map max drawdown onto a 0-100 fragility score.

    Judgment call: we treat a 60% peak-to-valley decline as "as bad as it
    gets" for this score (a 60 in a single position is a bear-market-plus
    move; a diversified portfolio falling 60% would be historic), and
    scale linearly from there — a 30% drawdown scores 50, a 15% drawdown
    scores 25. Drawdowns deeper than 60% are clipped to 100 rather than
    extrapolated further, since a score's job is to rank "how fragile,"
    not to keep counting past "very."
    """
    CAP = 0.60  # a 60% drawdown maps to the maximum score of 100

    dd = abs(max_drawdown(portfolio_returns(returns, weights)))
    return cap_and_scale(dd, CAP)


# ---------------------------------------------------------------------------
# 5. Volatility — "how wild is the ride?"
# ---------------------------------------------------------------------------


def daily_volatility(returns: pd.DataFrame) -> pd.Series:
    """
    Per-ticker standard deviation of *daily* returns — one number per
    column. Deliberately NOT annualized: the stress test's beta is a ratio
    of two volatilities (vol_target / vol_source), and that ratio is
    scale-invariant, so annualizing both sides by the same sqrt(252) would
    cancel out. Keeping it daily avoids the wasted work and the confusion.
    """
    return returns.std()


def annualized_volatility(portfolio_daily_returns: pd.Series) -> float:
    """
    The standard deviation of daily returns, scaled up to a yearly figure
    via the sqrt(time) rule: variance scales linearly with time, so
    standard deviation (its square root) scales with the square root of
    time. Multiplying the daily std dev by sqrt(252) turns a "boring"
    1%/day figure into a familiar "~16%/year" one that's comparable to
    numbers reported elsewhere.
    """
    daily_std = float(portfolio_daily_returns.std())
    return daily_std * np.sqrt(TRADING_DAYS_PER_YEAR)


def volatility_score(returns: pd.DataFrame, weights: dict[str, float]) -> float:
    """
    Map annualized portfolio volatility onto a 0-100 fragility score.

    Judgment call: we treat 50% annualized volatility as "as wild as it
    gets" for this score — that's roughly triple the long-run volatility
    of the S&P 500 (~15-20%/year), the territory of concentrated
    single-stock or leveraged portfolios — and scale linearly, clipping
    anything wilder to 100. A calm, diversified portfolio around 15%/year
    scores 30; an all-tech, high-beta basket around 35%/year scores 70.
    """
    CAP = 0.50  # 50% annualized volatility maps to the maximum score of 100

    vol = annualized_volatility(portfolio_returns(returns, weights))
    return cap_and_scale(vol, CAP)

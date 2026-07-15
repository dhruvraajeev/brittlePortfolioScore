"""
data — turn ticker symbols into the one object everything downstream
needs: a DataFrame of daily percent returns, plus a clean weights dict.

Nothing in this file computes risk. It only fetches and reshapes data.
Keeping "get the data" separate from "do math on the data" means
metrics.py can be unit-tested with made-up numbers and never has to touch
the network — see tests/test_engine.py, which never calls fetch_prices.
"""

from __future__ import annotations

import pandas as pd
import yfinance as yf


def fetch_prices(tickers: list[str], period: str = "2y") -> pd.DataFrame:
    """
    Download daily *adjusted* close prices for each ticker and return them
    as one DataFrame: one column per ticker, one row per trading day.

    We use adjusted close (not raw close) because raw prices jump around
    stock splits and dividend payouts in ways that have nothing to do with
    actual risk — a 2-for-1 split would otherwise look like a -50% crash.
    Adjusting folds those events out so the price series reflects only real
    gains/losses to someone holding the stock.
    """
    if not tickers:
        raise ValueError("fetch_prices needs at least one ticker")

    raw = yf.download(
        tickers,
        period = period,
        auto_adjust=True,  # yfinance returns split/dividend-adjusted OHLC
        progress=False,
    )

    if raw.empty:
        raise ValueError(f"no price data returned for: {', '.join(tickers)}")

    # yf.download always returns MultiIndex columns (e.g. ("Close", "AAPL"))
    # when `tickers` is a list — including a one-element list — in the
    # yfinance version this was built and tested against. The flat-column
    # shape only shows up if you pass a bare string instead of a list,
    # which fetch_prices never does. We still guard for it defensively in
    # case a future/older yfinance release changes that, since it costs
    # nothing and fails safe either way.
    if isinstance(raw.columns, pd.MultiIndex):
        prices = raw["Close"]
    else:
        prices = raw[["Close"]]
        prices.columns = tickers

    # Drop rows where *every* ticker is missing (e.g. an exchange holiday
    # that hit every symbol). We deliberately don't drop rows where only
    # *some* tickers are missing here — to_returns() below handles that,
    # because dropping too early can silently shrink the history of a
    # newer stock down to nothing.
    prices = prices.dropna(how="all")

    missing = [t for t in tickers if t not in prices.columns]
    if missing:
        raise ValueError(f"no price data returned for: {', '.join(missing)}")

    # A ticker yfinance can't resolve (typo, delisted, wrong exchange)
    # does NOT get omitted or raise when it's part of a multi-ticker
    # request — it silently comes back as a column of all-NaN prices
    # sitting right alongside its valid siblings. Left unchecked, that
    # NaN column survives dropna(how="all") (the other tickers keep every
    # row non-empty) and only blows up much later in to_returns() as a
    # baffling "no overlapping trading days" error that names no ticker.
    # Catch it here, at the source, with the ticker's name attached.
    unresolved = [t for t in tickers if prices[t].isna().all()]
    if unresolved:
        raise ValueError(f"no price data returned for: {', '.join(unresolved)}")

    return prices


def to_returns(prices: pd.DataFrame) -> pd.DataFrame:
    """
    Convert a price DataFrame into daily percent returns.

    This is "the foundation" conversion: a $5 move on a
    $50 stock and a $5 move on a $500 stock are not the same event, but a 1%
    move on each is directly comparable. Every metric downstream —
    volatility, correlation, the covariance matrix, PCA — operates on
    returns, never on raw prices. Get this step wrong and every number that
    follows is wrong too.

    We use *simple* returns (today / yesterday − 1), not log returns,
    because "you were up 1.3% today" is the number a person actually wants
    in the narrative. Log returns compound more cleanly over time, which is
    why quants often prefer them internally, but they're less legible to
    show a user directly.

    Rows with any missing value are dropped entirely (not filled): a single
    missing day for one ticker — a late IPO, a mismatched holiday calendar
    between a US stock and a foreign one — would otherwise poison every
    pairwise correlation and covariance number that includes that day.
    """
    returns = prices.pct_change()
    returns = returns.dropna(how="any")

    if returns.empty:
        raise ValueError(
            "no overlapping trading days across all tickers — check that "
            "every ticker has price history over the requested period"
        )

    return returns


def normalize_weights(weights: dict[str, float]) -> dict[str, float]:
    """
    Rescale a dict of {ticker: raw_weight} so the values sum to exactly 1.0.

    The UI hands us "something proportional" — dollar amounts, share
    counts, slider percentages that don't quite add to 100 after rounding —
    and this is the one place that turns "proportional" into a proper
    portfolio weight that every metric can multiply against safely.
    """
    if not weights:
        raise ValueError("normalize_weights needs at least one holding")

    total = sum(weights.values())
    if total <= 0:
        raise ValueError("weights must sum to a positive number")

    return {ticker: w / total for ticker, w in weights.items()}

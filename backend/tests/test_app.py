"""
Tests for the API layer (app.py) — the one file that touches HTTP.

These exercise the request-cleaning, the price cache, and the route handlers
by calling them directly, so no live server (or network) is needed. The
handlers are plain functions; FastAPI's serialization/routing is its own
concern and not re-tested here.
"""

from __future__ import annotations

import numpy as np
import pandas as pd
import pytest
from fastapi import HTTPException

import app as api
from app import AnalyzeRequest, _clean, _returns_for, analyze_endpoint, health


@pytest.fixture(autouse=True)
def _clear_price_cache():
    """Each test starts from a cold cache so hit/miss assertions are clean."""
    api._price_cache.clear()
    yield
    api._price_cache.clear()


def _fake_prices(tickers, periods=250):
    """A deterministic upward price series per ticker — enough rows that
    to_returns() yields a non-empty returns frame."""
    idx = np.arange(periods, dtype=float)
    return pd.DataFrame({t: 100.0 + idx + hash(t) % 5 for t in tickers})


# ---------------------------------------------------------------------------
# _clean — ticker/weight normalization
# ---------------------------------------------------------------------------


def test_clean_uppercases_and_strips():
    tickers, weights = _clean([" nvda ", "amd"], None)
    assert tickers == ["NVDA", "AMD"]
    # No weights supplied -> equal (1.0) default each.
    assert weights == {"NVDA": 1.0, "AMD": 1.0}


def test_clean_merges_duplicates_summing_weights():
    tickers, weights = _clean(["AAPL", "aapl"], {"AAPL": 2.0, "aapl": 3.0})
    assert tickers == ["AAPL"]
    assert weights == {"AAPL": pytest.approx(5.0)}


def test_clean_drops_blanks():
    tickers, _ = _clean(["", "   ", "MSFT"], None)
    assert tickers == ["MSFT"]


def test_clean_raises_on_empty():
    with pytest.raises(ValueError):
        _clean([], None)
    with pytest.raises(ValueError):
        _clean(["", "  "], None)


# ---------------------------------------------------------------------------
# _returns_for — the price cache (hit/miss, fetch only what's missing)
# ---------------------------------------------------------------------------


def test_returns_for_fetches_only_missing(monkeypatch):
    calls: list[list[str]] = []

    def fake_fetch(tickers, period="2y"):
        calls.append(list(tickers))
        return _fake_prices(tickers)

    monkeypatch.setattr(api, "fetch_prices", fake_fetch)

    # Cold cache: both tickers fetched, in one call.
    _returns_for(["AAA", "BBB"], "1y")
    assert calls == [["AAA", "BBB"]]

    # Warm cache: same request touches the network zero more times.
    _returns_for(["AAA", "BBB"], "1y")
    assert calls == [["AAA", "BBB"]]

    # Adding one ticker fetches ONLY the new one (per-ticker caching).
    _returns_for(["AAA", "BBB", "CCC"], "1y")
    assert calls == [["AAA", "BBB"], ["CCC"]]


def test_returns_for_period_is_part_of_the_key(monkeypatch):
    calls: list[tuple[list[str], str]] = []

    def fake_fetch(tickers, period="2y"):
        calls.append((list(tickers), period))
        return _fake_prices(tickers)

    monkeypatch.setattr(api, "fetch_prices", fake_fetch)

    _returns_for(["AAA"], "1y")
    _returns_for(["AAA"], "2y")  # same ticker, different period -> a real miss
    assert calls == [(["AAA"], "1y"), (["AAA"], "2y")]


# ---------------------------------------------------------------------------
# Route handlers
# ---------------------------------------------------------------------------


def test_health():
    assert health() == {"status": "ok"}


def test_analyze_endpoint_maps_bad_input_to_400():
    with pytest.raises(HTTPException) as exc:
        analyze_endpoint(AnalyzeRequest(tickers=[]))
    assert exc.value.status_code == 400


def test_analyze_endpoint_returns_full_payload(monkeypatch):
    # Synthetic correlated returns so we never touch the network; the real
    # engine runs on them.
    rng = np.random.default_rng(1)
    market = rng.normal(0, 0.01, 300)
    frame = pd.DataFrame(
        {f"T{i}": 0.7 * market + 0.3 * rng.normal(0, 0.01, 300) for i in range(4)}
    )
    monkeypatch.setattr(api, "_returns_for", lambda tickers, period: frame)

    result = analyze_endpoint(AnalyzeRequest(tickers=list(frame.columns)))
    for key in ("score", "verdict", "branches", "spof", "tail", "narrative"):
        assert key in result
    assert result["spof"]["ticker"] in frame.columns

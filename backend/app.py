"""
app — the FastAPI service that wraps the engine in JSON over HTTP.

This is the ONLY place that touches HTTP. It does three jobs and no math:
  1. Parse and validate the request (clean 400s for bad tickers, not stack
     traces).
  2. Fetch price data — cached per ticker so the live what-if slider, which
     only changes weights, never re-downloads anything.
  3. Call engine.analyze() and return the result.

Run it with:  uvicorn app:app --reload --port 8000
"""

from __future__ import annotations

import threading

import pandas as pd
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from engine import analyze, fetch_prices, to_returns

app = FastAPI(title="Portfolio Fragility Score", version="1.0.0")

# The React dev server (Vite) runs on 5173; allow it plus common local
# origins. Widen or lock this down when you deploy.
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:4173",
    ],
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---------------------------------------------------------------------------
# Price cache — the reason the live slider feels instant
# ---------------------------------------------------------------------------
# Adjusted-close series keyed by (ticker, period). yfinance is slow and rate
# limited, so we fetch each ticker once and reassemble the returns DataFrame
# from cache on every subsequent request. A weight change touches no network;
# adding a ticker fetches only that one. The lock guards the dict against
# concurrent requests hitting the same cold ticker.
_price_cache: dict[tuple[str, str], pd.Series] = {}
_cache_lock = threading.Lock()


def _returns_for(tickers: list[str], period: str) -> pd.DataFrame:
    """Assemble a daily-returns DataFrame, fetching only uncached tickers."""
    with _cache_lock:
        missing = [t for t in tickers if (t, period) not in _price_cache]
        if missing:
            prices = fetch_prices(missing, period=period)  # raises ValueError on bad tickers
            for t in missing:
                _price_cache[(t, period)] = prices[t]
        frame = pd.DataFrame({t: _price_cache[(t, period)] for t in tickers})
    return to_returns(frame)


def _clean(tickers: list[str], weights: dict[str, float] | None) -> tuple[list[str], dict[str, float]]:
    """
    Normalize user input: uppercase/strip tickers, drop blanks, merge
    duplicates (summing their weights), and default to equal weight when no
    weights are supplied. Raises ValueError (→ 400) on empty input.
    """
    seen: list[str] = []
    merged: dict[str, float] = {}
    wdict = weights or {}
    for raw in tickers:
        t = (raw or "").strip().upper()
        if not t:
            continue
        w = wdict.get(raw, wdict.get(t, 1.0))
        if t in merged:
            merged[t] += w
        else:
            merged[t] = w
            seen.append(t)

    if not seen:
        raise ValueError("Enter at least one ticker.")
    return seen, {t: merged[t] for t in seen}


# ---------------------------------------------------------------------------
# Request models
# ---------------------------------------------------------------------------


class AnalyzeRequest(BaseModel):
    tickers: list[str] = Field(..., description="Ticker symbols, e.g. ['NVDA','AMD']")
    weights: dict[str, float] | None = Field(
        None, description="Optional {ticker: weight}; equal-weighted if omitted"
    )
    period: str = Field("1y", description="yfinance history window, e.g. '6mo','1y','2y'")
    include_var: bool = True


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------


@app.get("/api/health")
def health() -> dict:
    return {"status": "ok"}


@app.post("/api/analyze")
def analyze_endpoint(req: AnalyzeRequest) -> dict:
    """
    Analyze a portfolio. The primary endpoint — the live slider hits this on
    every (debounced) change. Returns the full analysis.
    """
    try:
        tickers, weights = _clean(req.tickers, req.weights)
        returns = _returns_for(tickers, req.period)
        return analyze(returns, weights, include_var=req.include_var)
    except ValueError as e:
        # Bad/empty/unknown tickers, no overlapping history — a user error,
        # surfaced as a calm 400 rather than a 500 stack trace.
        raise HTTPException(status_code=400, detail=str(e))

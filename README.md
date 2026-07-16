# Brittle

A playground or sandbox for a given stock portfolio, displaying a hidden fragility metric. Add some tickers, drag the weight sliders, and watch a single 0-100 **Fragility Score** as a way to build stock diversity intuition, in finding the one holding that would affect you most.

## What it does

Given a set of tickers and weights, Brittle pulls price history and answers three questions:

- **How fragile is this portfolio?** One headline score (0–100), split into three risk branches: position sizing, co-movement, and tail risk.
- **What's my single point of failure?** The holding most tied to the portfolio's dominant hidden factor, and how much *worse* a crash in it would hurt than its weight alone suggests (the "amplification").
- **Why?** A radar of six sub-scores, branch bars, tail stats (volatility, drawdown, VaR/CVaR), and a summary regarding the stats of your portfolio.

Everything recomputes as you drag sliders, so you can feel how diversifying your portfolio moves the number.

## How it works

Three layers, deliberately kept separate:

```
frontend/  React + Vite UI — sliders, gauge, charts. Does zero finance math.
backend/   FastAPI service. The only layer that touches HTTP.
engine/  Pure Python analysis. No web framework, no network (except price fetch).
```

- The **engine** turns prices into daily returns, then computes correlation, concentration (HHI), a hidden-factor share (PCA via NumPy SVD), drawdown, volatility, and historical VaR/CVaR. These roll up into the branch scores and the final number.

- The **single point of failure** is found by weighting each holding's exposure to the dominant hidden factor (PC1), then modeling a 30% shock and letting correlated holdings fall alongside it.

- The **API** validates input, caches prices per ticker (so dragging a weight slider never re-downloads data), and calls the engine once per request.

- The **frontend** debounces slider changes and calls `/api/analyze`, then renders the result.

## Running locally

Requires Python 3.11+ and Node 18+.

```bash
# 1. Backend deps (into a virtualenv)
python3 -m venv .venv
.venv/bin/pip install -r backend/requirements.txt

# 2. Frontend + root deps
npm run install:all

# 3. Run backend + frontend together
npm run dev
```

Additionally, the project can be viewed at:

https://brittlepfs.vercel.app

## Tests

The engine and API are covered by network-free tests (synthetic return data):

```bash
.venv/bin/pytest backend
```

## Notes

- Prices come from Yahoo Finance via `yfinance`; availability and accuracy are whatever Yahoo returns.

- The score is an **ordinal heuristic** which is typically good for ranking "more vs. less fragile," and not a calibrated risk figure.

- Educational tool / something for you to mess around with. Not investment advice.

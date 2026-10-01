# Product

<!-- impeccable:product-schema 1 -->

## Platform

web

## Users

Primarily recruiters and engineers reviewing Dhruv's portfolio. They arrive from a résumé or personal site, spend a minute or two playing with it, and should leave understanding both what the tool computes and that its author knows quantitative risk and can build clean Python + TypeScript systems. Secondary: anyone curious about how diversified their own holdings really are.

## Product Purpose

Brittle takes a set of tickers and weights, pulls price history, and returns a 0–100 Fragility Score plus the single holding whose crash would hurt the portfolio most (the single point of failure, SPOF) and how much worse than its weight that crash would be (amplification). Everything recomputes live as weights change, so the user builds intuition about diversification by feel.

Success: a visitor grasps score + SPOF within seconds, drags a slider, sees cause → effect, and comes away with an impression of quantitative competence and engineering restraint.

## Positioning

It looks past ticker labels to hidden shared risk: PCA (SVD) dominant-factor exposure, correlation, HHI concentration, drawdown, volatility, historical VaR/CVaR, rolled into three branches (position sizing, co-movement, tail risk). The SPOF is found by weighting each holding's exposure to PC1 and modelling a 30% shock propagated through correlated holdings.

## Operating Context

Single-page tool. Desktop first (recruiters on laptops), must work on phones. Deployed at https://brittlepfs.vercel.app.

## Capabilities and Constraints

- Frontend: React 18 + Vite + Tailwind 3 + framer-motion. Does zero finance math; calls `POST /api/analyze`.
- Backend: FastAPI + pure-Python engine; prices from Yahoo Finance via yfinance.
- Periods: 6mo, 1y, 2y, 5y. At least one holding at all times.
- The score is an ordinal heuristic, not a calibrated risk figure.

## Brand Commitments

- Name: Brittle.
- Owner wants a dark interface with purple tints and accents only, clean and sleek, easy on the eyes, motion present but not heavy, not over-the-top. The project is a technical showcase, not a marketing piece.

## Evidence on Hand

Real computed output from the engine for any ticker set. No testimonials, users, or performance claims exist; none may be invented.

## Product Principles

1. The math is the star; the interface stays out of its way.
2. Every number is explained once, plainly, near where it appears.
3. Cause → effect must be instant and legible when a weight changes.
4. Restraint signals competence; no decoration that does not carry data.

## Accessibility & Inclusion

Respect prefers-reduced-motion; keep text contrast at WCAG AA on the dark ground; all controls keyboard-operable.

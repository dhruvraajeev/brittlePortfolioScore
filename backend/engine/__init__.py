"""
engine — the Portfolio Fragility Score engine.

Math and analysis. Nothing in this package imports FastAPI, touches HTTP, or
renders UI — `app.py` is the only thing that turns this into an HTTP
response, and `frontend/` is the only thing that renders it.

The one exception to "pure" is `data.fetch_prices`, the single seam that
reaches the network (yfinance). Everything downstream of a returns DataFrame
— every metric, score, and the whole of `analyze()` — is a deterministic
function of its inputs with no I/O, which is exactly why the tests can build
synthetic returns and never touch the network.

The public entry point is `analyze()`; everything else is a building block.
"""

from .analysis import analyze
from .data import fetch_prices, normalize_weights, to_returns
from .score import fragility_score, sub_scores

__all__ = [
    "analyze",
    "fragility_score",
    "sub_scores",
    "fetch_prices",
    "to_returns",
    "normalize_weights",
]

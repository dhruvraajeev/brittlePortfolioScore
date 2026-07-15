"""
engine.explain — turn the numbers into plain English.

A deterministic TEMPLATE narrative, built purely from the numbers: the
headline sentence and the plain-English overview. Everything here is a pure
function of the analysis dict — no network, no model, always the same output
for the same input, which is also what the tests assert on.
"""

from __future__ import annotations

_VERDICT_PHRASE = {
    "resilient": "holds together well",
    "moderate": "has some real soft spots",
    "fragile": "is dangerously concentrated",
}


def _pct(x: float) -> str:
    """Format a 0-1 fraction as a rounded percent, e.g. 0.263 -> '26%'."""
    return f"{round(x * 100)}%"


def attribution_sentence(analysis: dict) -> str:
    """
    The single most important human-readable line: name the single point of
    failure and quantify how much worse it is than it looks. Built straight
    from the SPOF numbers, no model needed.
    """
    spof = analysis["spof"]
    ticker = spof["ticker"]
    amp = spof["amplification"]
    real_loss = abs(spof["real_loss"])
    shock_pct = _pct(spof["shock"])

    return (
        f"{ticker} is your single point of failure. If it fell {shock_pct}, "
        f"your portfolio would drop about {_pct(real_loss)} — roughly "
        f"{amp:.1f}x worse than its weight alone suggests, because its "
        f"correlated holdings fall with it."
    )


def template_narrative(analysis: dict) -> str:
    """
    The deterministic 2-3 sentence narrative shown under the gauge. Built
    purely from the numbers, so it always agrees with them and is exactly
    reproducible — same analysis in, same sentence out, which is what the
    tests assert on.
    """
    verdict = analysis["verdict"]
    score = analysis["score"]
    hidden = analysis["hidden_factor_pct"]

    lead = (
        f"Your portfolio scores {score:.0f}/100 and {_VERDICT_PHRASE[verdict]}. "
    )
    factor = (
        f"About {_pct(hidden)} of its day-to-day movement traces back to a "
        f"single hidden force, so it behaves like fewer real bets than it looks. "
    )
    attribution = analysis.get("attribution") or attribution_sentence(analysis)
    return lead + factor + attribution

---
version: 1
slug: "frontend-src-app-tsx"
primary_target: "frontend/src/App.tsx"
related_targets: []
---

# Surface brief: Brittle app (single page)

Scope: the whole single-page tool. Mode: Operate. Audience: recruiters/engineers reviewing a quant + full-stack showcase; one to two minutes of play. Task: read score + SPOF, drag weights, see cause → effect. Quality bar: Linear + Raycast blend (user-chosen canon). Build path: code-led, no comp.

## Direction contract

THESIS: The category-standard dark analytics dashboard, executed at Linear/Raycast craft: an app shell with a headline panel and a controls column. Refuses decoration that carries no data (particles, glows, glass, radar for its own sake).

OWN-WORLD: Near-black ground tinted violet (#0b0a0f), two raised surfaces one step apart, 1px violet-tinted hairlines, a single lavender accent (#a594ff) for interactive state and data ink; verdict hues muted (mint/amber/rose) only on verdict-bearing values. Geist for UI and every figure (tabular numerals); Geist Mono for tickers only, because mono numerals read loose and costume-like at display size. 10px panel radii, no shadows beyond one soft elevation on popovers.

STORY: Visitor sees one question and the answer immediately (score + SPOF), hovers a holding and sees its exposure light up, drags a fader and watches the score glide, then reads how the score is composed and how bad the tail gets.

FIRST VIEWPORT: Top bar (mark + name left, period segmented control + live status right). Title question + one-line subtitle. SPOF side carries a weight-alone vs correlated loss bar pair, because it is the visual proof of the amplification figure. Headline panel full width: score (large tabular figure, verdict, 0–100 band meter with damped indicator) | SPOF (ticker, amplification, consequence sentence). Below: holdings column (command-style add input, fader rows) left 5/12; composition + factor exposure right 7/12.

FORM: canon (category standard), user-picked; seed key 481d5ca6.

FINISH: unreviewed and undocumented is unfinished; this build ends with the finish review, the verdict, DESIGN.md, and every shipping raster carrying its provenance

---
name: Brittle
description: A dark, violet-tinted analytics instrument that names a portfolio's single point of failure.
colors:
  bg: "#0b0a0f"
  panel: "#111017"
  raised: "#18161f"
  line: "rgba(178, 164, 255, 0.08)"
  line-strong: "rgba(178, 164, 255, 0.16)"
  fg: "#ecebf3"
  fg-2: "#aaa6b9"
  fg-3: "#847f97"
  accent: "#a594ff"
  ok: "#6fd0a6"
  warn: "#e3bd6d"
  bad: "#f0808f"
typography:
  display:
    fontFamily: "Geist, system-ui, sans-serif"
    fontSize: "76px"
    fontWeight: 500
    lineHeight: 1
    letterSpacing: "-0.04em"
    fontFeature: "\"tnum\" 1"
  headline:
    fontFamily: "Geist, system-ui, sans-serif"
    fontSize: "32px"
    fontWeight: 500
    lineHeight: 1.2
    letterSpacing: "-0.025em"
  ticker-display:
    fontFamily: "Geist Mono, ui-monospace, monospace"
    fontSize: "40px"
    fontWeight: 500
    lineHeight: 1
    letterSpacing: "-0.03em"
  title:
    fontFamily: "Geist, system-ui, sans-serif"
    fontSize: "13px"
    fontWeight: 500
    lineHeight: 1.5
  body:
    fontFamily: "Geist, system-ui, sans-serif"
    fontSize: "14px"
    fontWeight: 400
    lineHeight: 1.5
  label:
    fontFamily: "Geist, system-ui, sans-serif"
    fontSize: "12px"
    fontWeight: 400
    lineHeight: 1.5
  ticker:
    fontFamily: "Geist Mono, ui-monospace, monospace"
    fontSize: "13px"
    fontWeight: 500
    lineHeight: 1.5
    letterSpacing: "-0.01em"
rounded:
  sm: "2px"
  md: "6px"
  lg: "8px"
  panel: "10px"
  full: "999px"
spacing:
  xs: "8px"
  sm: "12px"
  md: "16px"
  lg: "20px"
  xl: "24px"
  2xl: "40px"
components:
  panel:
    backgroundColor: "{colors.panel}"
    rounded: "{rounded.panel}"
  panel-head:
    textColor: "{colors.fg}"
    typography: "{typography.title}"
    padding: "14px 20px"
  segmented-control:
    backgroundColor: "{colors.panel}"
    textColor: "{colors.fg-3}"
    rounded: "{rounded.lg}"
    padding: "2px"
  segmented-control-option:
    textColor: "{colors.fg-3}"
    typography: "{typography.label}"
    rounded: "{rounded.md}"
    padding: "4px 10px"
  segmented-control-option-active:
    backgroundColor: "{colors.raised}"
    textColor: "{colors.fg}"
  command-input:
    backgroundColor: "{colors.bg}"
    textColor: "{colors.fg}"
    typography: "{typography.ticker}"
    rounded: "{rounded.lg}"
    height: "40px"
    padding: "0 12px"
  key-button:
    textColor: "{colors.fg-2}"
    rounded: "{rounded.md}"
    height: "24px"
    width: "28px"
  key-button-hover:
    backgroundColor: "{colors.raised}"
    textColor: "{colors.fg}"
  fader-row:
    rounded: "{rounded.lg}"
    padding: "8px 12px"
  fader-row-hover:
    backgroundColor: "{colors.raised}"
  icon-button:
    textColor: "{colors.fg-3}"
    rounded: "{rounded.md}"
    size: "28px"
  verdict-pill:
    typography: "{typography.label}"
    rounded: "{rounded.full}"
    padding: "2px 8px"
  stat-cell:
    backgroundColor: "{colors.panel}"
    padding: "16px 20px"
  error-banner:
    textColor: "{colors.bad}"
    rounded: "{rounded.lg}"
    padding: "12px 16px"
---

# Design System: Brittle

## Overview

**Creative North Star: "The Quiet Instrument"**

Brittle is the category-standard dark analytics dashboard held to Linear and Raycast craft: an app shell, one full-width headline panel that answers the question, and a two-column working area beneath it. The ground is near-black tinted violet; surfaces rise one small tonal step at a time and are separated by hairlines rather than shadow. Everything that is not data recedes into three grey-violet text tiers, so the few saturated marks on screen (the lavender accent and the three muted verdict hues) are always carrying a number.

Density is compact and calm: 14px body, 13px panel titles, 12px metadata, generous panel padding, and large figures only where the answer lives (the score and the SPOF ticker). Motion is present but brief: values glide to their new state with one long-tailed ease-out curve, bars resize rather than redraw, and every authored animation yields to reduced-motion preferences.

The world refuses decoration that carries no data: no particles, no glows, no glass panels, no radar or ornament for its own sake.

**Key Characteristics:**
- Violet-tinted near-black ground with two raised surfaces one step apart.
- 1px violet-tinted hairlines do the structural work shadows would do elsewhere.
- One lavender accent for interactive state and data ink; verdict hues only on verdict-bearing values.
- Geist for all UI and every figure with tabular numerals; Geist Mono for tickers only.
- 10px panel radius, 8px for inner controls, 6px for small buttons, full pills for bars and dots.
- Short, damped motion on a single ease-out curve.

## Colors

A monochrome violet-grey scale with one lavender voice and three muted verdict hues.

### Primary
- **Lavender Signal** (accent): the only interactive and data-ink color. Fader fill, caret, focus ring, the brand mark, the loading sweep, exposure bars for non-SPOF holdings, and the stacked composition bar (stepped as 100% / 62% / 36% mixes of itself, never a second hue).

### Verdict hues
- **Muted Mint** (ok): the Resilient band and the "Live" status dot.
- **Muted Amber** (warn): the Moderate band.
- **Muted Rose** (bad): the Fragile band, the SPOF dot, the SPOF exposure bar, the correlated-loss bar, the amplification figure, and error text.

### Neutral
- **Violet Night** (bg): page ground, the sticky header (at 82% opacity), and the recessed command input.
- **Panel Ink** (panel): every panel and stat cell, and the segmented control's well.
- **Raised Ink** (raised): hover fill on rows and small buttons; the active segmented option.
- **Hairline** (line): panel borders, panel-head and section dividers, table rules, the 1px gap between stat cells.
- **Strong Hairline** (line-strong): the active segmented option's inset ring and the submit key's border.
- **Moonlit Text** (fg): primary text and figures; also the fader thumb and the score indicator.
- **Dusk Text** (fg-2): secondary copy, subtitles, sub-labels, non-SPOF tickers.
- **Haze Text** (fg-3): metadata, scale labels, placeholders, icons at rest. It holds 4.66:1 even on raised, so it remains AA for small text.

### Named Rules
**The One Voice Rule.** Lavender is the only hue that marks interaction or neutral data. A second accent never appears; gradations come from mixing lavender with transparency.

**The Earned Hue Rule.** Mint, amber, and rose appear only on values that carry a verdict (score band, verdict pill, SPOF marks, loss amplification, errors). They are tinted into chips and tracks with `color-mix` at 8 to 34%, never used as fills for chrome.

**The Tinted Track Rule.** Empty tracks and bar wells are lavender at very low alpha (about 6%), not grey, so the ground stays in one hue family.

## Typography

**Display Font:** Geist (with system-ui, sans-serif)
**Body Font:** Geist (with system-ui, sans-serif)
**Label/Mono Font:** Geist Mono (with ui-monospace, monospace), tickers only

**Character:** A single neo-grotesk does the whole job, tightened with negative tracking as size grows; tabular numerals keep live figures from jittering. Mono is reserved for ticker symbols, where it reads as an identifier, never for figures, where it would read loose and costume-like at display size.

### Hierarchy
- **Display** (500, 64px mobile / 76px from 640px, line-height 1, -0.04em, tabular): the fragility score, once per page.
- **Headline** (500, 26px mobile / 32px from 640px, line-height 1.2, -0.025em, balanced wrap, max ~42rem): the page question.
- **Ticker Display** (Geist Mono 500, 40px, line-height 1, -0.03em): the SPOF symbol.
- **Figures** (500 at 24px for amplification; 400 at 20px for stat cells; 15px for composition points): secondary numbers, always tabular.
- **Title** (500, 13px): panel titles and in-panel section headings (headline-panel headings use Dusk Text).
- **Body** (400, 14px, line-height 1.5; 13px for row text and explanatory sentences at relaxed leading): copy and row values.
- **Label** (400, 12px; 11px for the score scale): metadata, table headers, hints, status.
- **Ticker** (Geist Mono 500, 13px, -0.01em, uppercase): every ticker in rows and inputs.
- **Wordmark** (600, 15px, -0.01em): "Brittle" in the top bar only.

### Named Rules
**The Tabular Figures Rule.** Every number that can change is set with tabular numerals (`num`), so live updates move digits, not layout.

**The Mono Means Ticker Rule.** Geist Mono is for ticker symbols only; scores, percentages, and amounts stay in Geist.

## Layout

A centered shell capped at 1152px with 16px side padding (24px from 640px). A 56px sticky top bar holds the mark and wordmark on the left, status and period control on the right. The page opens with the headline question and a one-line subtitle (40px top padding, 56px from 640px), then the full-width headline panel, then a 12-column grid with 16px gaps: holdings in the left five columns (sticky at 80px from the top on wide screens), analysis panels stacked in the right seven with 16px between them.

Responsive behavior: below 768px the headline panel stacks score above SPOF with a hairline between; from 768px it splits 1.15fr / 1fr with a vertical hairline. Below 1024px the working grid collapses to one column. Secondary metadata in panel heads hides below 640px; the remove button on holding rows is always visible on devices without hover.

Spacing rhythm is a 4px base: 8 and 12px inside rows, 16px between panels, 20px panel padding (24px in the headline panel from 640px), 24 to 32px between page sections.

**The Answer First Rule.** Score and SPOF sit above everything else at full width; explanatory panels come after, never before.

## Elevation & Depth

Flat by construction. Depth comes from tonal steps (bg, panel, raised) and 1px violet hairlines, not from drop shadows. Panels carry one faint inset top highlight that reads as an edge catching light. The only other shadows are functional: a small contact shadow under the fader thumb, an inset ring on the active segmented option, and a 3px panel-colored ring that cuts the score indicator out of the band meter. The sticky header uses translucency with a backdrop blur purely so scrolled content stays legible under it.

### Shadow Vocabulary
- **Panel edge** (`box-shadow: inset 0 1px 0 rgba(255, 255, 255, 0.035)`): every panel.
- **Thumb contact** (`box-shadow: 0 1px 3px rgba(0, 0, 0, 0.5)`): fader thumb only.
- **Selected ring** (`box-shadow: inset 0 0 0 1px var(--line-strong)`): the active segmented option.
- **Cut-out ring** (`box-shadow: 0 0 0 3px var(--panel)`): the score indicator over its band meter.

### Named Rules
**The Hairline Not Shadow Rule.** Separate surfaces with a 1px hairline and a tonal step. A drop shadow is never used to lift a panel.

## Shapes

Gently rounded and consistent by tier: panels at 10px, inner controls (input, segmented well, rows, error banner) at 8px, small buttons and the segmented pill at 6px, the composition legend swatch at 2px, and every bar, track, dot, and verdict pill fully rounded. The focus ring follows at 6px with a 2px offset. Tracks are thin (4 to 10px tall). The brand mark is a softly rounded tile split by a single fracture line.

## Components

### Buttons
- **Character:** small, quiet, keyboard-shaped.
- **Key button (submit):** 28 by 24px, 6px radius, Strong Hairline border, Dusk Text icon; hover fills Raised Ink and brightens to Moonlit Text; disabled at 40% opacity.
- **Icon button (remove):** 28px square, 6px radius, Haze Text; hidden until its row is hovered or focused (always shown without hover); hover fills lavender at 8%.
- **Focus:** global 2px lavender outline, 2px offset.

### Chips
- **Verdict pill:** full radius, 2px by 8px, 12px medium text in the verdict hue over the same hue at 12%, led by a 6px dot of the hue.

### Cards / Containers
- **Panel:** Panel Ink, 10px radius, Hairline border, inset edge highlight. A panel head (title left, metadata right, baseline aligned, 14px by 20px, hairline below) precedes the body.
- **Stat cell:** Panel Ink cells laid in a grid whose 1px gap shows the hairline through.

### Inputs / Fields
- **Command input:** recessed (Violet Night) 40px field with 8px radius, Hairline border, leading search icon, Geist Mono uppercase entry with a sans placeholder, and a trailing Enter key button. Focus shifts the border to lavender at 45%; the native outline is suppressed inside it. "/" focuses it from anywhere.

### Navigation
- **Top bar:** sticky, 56px, Violet Night at 82% with backdrop blur, hairline below.
- **Segmented control:** Panel Ink well, 8px radius, 2px padding; options are 12px tabular labels in Haze Text (Dusk Text on hover); the active option sits on a Raised Ink pill with an inset Strong Hairline ring that slides between options on a stiff spring.

### Fader Row (signature)
A four-column row: ticker (with a rose dot if it is the SPOF), a fader, the normalized share in tabular figures, and a reveal-on-hover remove button. The fader is a 4px full-radius track filled with lavender to the raw weight over lavender at 12%, with a 14px Moonlit Text thumb that grows 12% on hover. Hovering a row fills it with Raised Ink and dims every other holding across the page to about 40 to 45%, linking the input to its exposure.

### Band Meter (signature)
The score scale as three fully rounded segments (0 to 30 mint, 30 to 60 amber, 60 to 100 rose) separated by 3px gaps. All segments rest at 12% of their hue; the active verdict's segment rises to 34%. A 3 by 20px Moonlit Text indicator, cut out with a panel-colored ring, springs to the score with a damped settle.

### Loss Bar Pair (signature)
Two 6px bars on a shared scale: "By weight alone" in Haze Text and "With correlated holdings" in Muted Rose, label left and tabular loss right. The visible gap between them is the amplification.

### Bar rows
Exposure and composition use the same 6 to 10px full-radius tracks on lavender at about 6%. Bars animate width over 600ms on the shared ease-out curve; they never redraw from zero on update.

## Do's and Don'ts

### Do:
- **Do** use Lavender Signal for every interactive state and every neutral data mark, and nothing else.
- **Do** set every live figure in Geist with tabular numerals.
- **Do** separate surfaces with a 1px hairline and one tonal step (bg, panel, raised).
- **Do** tint verdict hues into chips and tracks with `color-mix` (8 to 34%) rather than using them as solid chrome.
- **Do** animate value changes on the shared ease-out curve `cubic-bezier(0.16, 1, 0.3, 1)` within 160 to 700ms, and let reduced-motion users get the end state.
- **Do** link a hovered holding to every figure that mentions it by dimming the others.

### Don't:
- **Don't** add particles, glows, glass panels, or decorative charts that carry no data.
- **Don't** introduce a second accent hue or a gradient fill beyond the transparent lavender loading sweep.
- **Don't** set figures in Geist Mono; mono is for tickers.
- **Don't** lift panels with drop shadows.
- **Don't** use mint, amber, or rose on anything that is not a verdict, a SPOF mark, or an error.

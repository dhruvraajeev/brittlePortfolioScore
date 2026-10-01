import { AnimatePresence, motion } from "framer-motion";
import { useEffect, useRef, useState } from "react";
import type { Holding } from "../App";
import { EASE, normalizedWeights } from "../lib/format";
import { Close, Enter, Search } from "./Icons";

/**
 * The input surface: add tickers from a command-style field and set each
 * holding's weight with a fader. Hovering a row highlights that holding in
 * every figure on the page.
 */
export default function Holdings({
  holdings,
  spofTicker,
  focus,
  onFocus,
  onAdd,
  onRemove,
  onWeightChange,
}: {
  holdings: Holding[];
  spofTicker?: string;
  focus: string | null;
  onFocus: (ticker: string | null) => void;
  onAdd: (ticker: string) => void;
  onRemove: (ticker: string) => void;
  onWeightChange: (ticker: string, weight: number) => void;
}) {
  const [draft, setDraft] = useState("");
  const inputRef = useRef<HTMLInputElement>(null);

  // "/" focuses the add field from anywhere, like a command bar.
  useEffect(() => {
    const onKey = (e: KeyboardEvent) => {
      const typing = e.target instanceof HTMLInputElement || e.target instanceof HTMLTextAreaElement;
      if (e.key === "/" && !typing) {
        e.preventDefault();
        inputRef.current?.focus();
      }
    };
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, []);
  const shares = normalizedWeights(Object.fromEntries(holdings.map((h) => [h.ticker, h.weight])));

  function submit(e: React.FormEvent) {
    e.preventDefault();
    const t = draft.trim().toUpperCase();
    if (t) {
      onAdd(t);
      setDraft("");
    }
  }

  return (
    <section className="panel">
      <div className="panel-head">
        <h2 className="panel-title">Holdings</h2>
        <span className="meta hidden sm:inline">Weights normalize to 100%</span>
      </div>

      <form onSubmit={submit} className="border-b border-line p-3">
        <label className="group flex items-center gap-2.5 rounded-lg border border-line bg-bg px-3 transition-colors focus-within:border-[rgba(165,148,255,0.45)]">
          <Search className="h-4 w-4 shrink-0 text-fg3" />
          <input
            ref={inputRef}
            value={draft}
            onChange={(e) => setDraft(e.target.value)}
            placeholder="Add a ticker, e.g. MSFT"
            aria-label="Add a ticker"
            autoComplete="off"
            spellCheck={false}
            className="ticker h-10 min-w-0 flex-1 bg-transparent text-[13px] uppercase text-fg outline-none placeholder:font-sans placeholder:normal-case placeholder:text-fg3 focus-visible:outline-none"
          />
          <button
            type="submit"
            aria-label="Add ticker"
            disabled={!draft.trim()}
            className="grid h-6 w-7 place-items-center rounded-md border border-line2 text-fg2 transition-colors hover:bg-raised hover:text-fg disabled:opacity-40"
          >
            <Enter className="h-3.5 w-3.5" />
          </button>
        </label>
      </form>

      <ul className="p-1.5" onMouseLeave={() => onFocus(null)}>
        <AnimatePresence initial={false}>
          {holdings.map((h) => {
            const share = shares[h.ticker] ?? 0;
            const isSpof = h.ticker === spofTicker;
            const dimmed = focus !== null && focus !== h.ticker;
            return (
              <motion.li
                key={h.ticker}
                layout="position"
                initial={{ opacity: 0, height: 0 }}
                animate={{ opacity: dimmed ? 0.45 : 1, height: "auto" }}
                exit={{ opacity: 0, height: 0 }}
                transition={{ duration: 0.3, ease: EASE }}
                onMouseEnter={() => onFocus(h.ticker)}
                onFocus={() => onFocus(h.ticker)}
                className="overflow-hidden"
              >
                <div className="group grid grid-cols-[4.5rem_1fr_3rem_1.75rem] items-center gap-3 rounded-lg px-3 py-2 transition-colors hover:bg-raised">
                  <div className="flex items-center gap-1.5">
                    <span className="ticker text-[13px] font-medium text-fg">{h.ticker}</span>
                    {isSpof && (
                      <span className="h-1.5 w-1.5 rounded-full bg-bad" title="Single point of failure" />
                    )}
                  </div>
                  <input
                    type="range"
                    min={0}
                    max={100}
                    value={Math.round(h.weight)}
                    onChange={(e) => onWeightChange(h.ticker, Number(e.target.value))}
                    aria-label={`${h.ticker} weight`}
                    aria-valuetext={`${Math.round(share * 100)}% of portfolio`}
                    style={{ ["--fill" as string]: `${h.weight}%` }}
                    className="w-full"
                  />
                  <span className="num text-right text-[13px] text-fg2">{Math.round(share * 100)}%</span>
                  <button
                    onClick={() => onRemove(h.ticker)}
                    disabled={holdings.length <= 1}
                    aria-label={`Remove ${h.ticker}`}
                    className="grid h-7 w-7 place-items-center rounded-md text-fg3 opacity-0 transition [@media(hover:none)]:opacity-100 hover:bg-[rgba(178,164,255,0.08)] hover:text-fg focus-visible:opacity-100 group-hover:opacity-100 disabled:hidden"
                  >
                    <Close className="h-3.5 w-3.5" />
                  </button>
                </div>
              </motion.li>
            );
          })}
        </AnimatePresence>
      </ul>
    </section>
  );
}

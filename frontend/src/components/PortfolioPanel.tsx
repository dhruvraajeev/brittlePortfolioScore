import { useState } from "react";
import type { Holding } from "../App";
import WeightSliders from "./WeightSliders";

/**
 * The left control panel: add/remove tickers, adjust weights (via
 * WeightSliders), and pick a history window. This is the input surface for
 * the whole app.
 */
export default function PortfolioPanel({
  holdings,
  period,
  spofTicker,
  loading,
  onAdd,
  onRemove,
  onWeightChange,
  onPeriodChange,
}: {
  holdings: Holding[];
  period: string;
  spofTicker?: string;
  loading: boolean;
  onAdd: (ticker: string) => void;
  onRemove: (ticker: string) => void;
  onWeightChange: (ticker: string, weight: number) => void;
  onPeriodChange: (period: string) => void;
}) {
  const [draft, setDraft] = useState("");

  function submit(e: React.FormEvent) {
    e.preventDefault();
    const t = draft.trim().toUpperCase();
    if (t) {
      onAdd(t);
      setDraft("");
    }
  }

  const periods = ["6mo", "1y", "2y", "5y"];

  return (
    <div className="card flex flex-col gap-5">
      <div className="flex items-center justify-between">
        <div className="label">Your portfolio</div>
        {loading && (
          <span className="flex items-center gap-1.5 text-xs text-sky-300">
            <span className="h-1.5 w-1.5 animate-ping rounded-full bg-sky-400" />
            recomputing
          </span>
        )}
      </div>

      <form onSubmit={submit} className="flex gap-2">
        <input
          value={draft}
          onChange={(e) => setDraft(e.target.value)}
          placeholder="Add ticker (e.g. NVDA)"
          className="min-w-0 flex-1 rounded-xl border border-white/10 bg-white/[0.04] px-3 py-2 text-sm text-white placeholder:text-white/30 focus:border-sky-400/60 focus:outline-none"
        />
        <button
          type="submit"
          className="rounded-xl bg-sky-500/90 px-4 py-2 text-sm font-semibold text-ink-900 transition hover:bg-sky-400"
        >
          Add
        </button>
      </form>

      <WeightSliders
        holdings={holdings}
        spofTicker={spofTicker}
        onWeightChange={onWeightChange}
        onRemove={onRemove}
      />

      <div className="flex items-center gap-1 border-t border-white/10 pt-4">
        {periods.map((p) => (
          <button
            key={p}
            onClick={() => onPeriodChange(p)}
            className={`rounded-lg px-2.5 py-1 text-xs font-semibold transition ${
              p === period
                ? "bg-sky-500/20 text-sky-300"
                : "text-white/40 hover:text-white/70"
            }`}
          >
            {p}
          </button>
        ))}
      </div>
    </div>
  );
}

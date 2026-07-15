import { AnimatePresence, motion } from "framer-motion";
import type { Holding } from "../App";
import { normalizedWeights } from "../lib/format";

/**
 * The live what-if simulator. One slider per holding; dragging recomputes
 * the score in real time (the parent debounces the API call). Weights are
 * shown as normalized percentages so they always read as "share of
 * portfolio," regardless of the raw slider values.
 */
export default function WeightSliders({
  holdings,
  spofTicker,
  onWeightChange,
  onRemove,
}: {
  holdings: Holding[];
  spofTicker?: string;
  onWeightChange: (ticker: string, weight: number) => void;
  onRemove: (ticker: string) => void;
}) {
  const weightsMap = Object.fromEntries(holdings.map((h) => [h.ticker, h.weight]));
  const normalized = normalizedWeights(weightsMap);

  return (
    <div className="space-y-3">
      <AnimatePresence initial={false}>
        {holdings.map((h) => {
          const sharePct = Math.round((normalized[h.ticker] ?? 0) * 100);
          const isSpof = h.ticker === spofTicker;
          return (
            <motion.div
              key={h.ticker}
              layout
              initial={{ opacity: 0, height: 0 }}
              animate={{ opacity: 1, height: "auto" }}
              exit={{ opacity: 0, height: 0 }}
              transition={{ duration: 0.25 }}
            >
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <span className="font-semibold text-white/90">{h.ticker}</span>
                  {isSpof && (
                    <span className="chip border-fragile/40 bg-fragile/10 text-fragile">
                      SPOF
                    </span>
                  )}
                </div>
                <div className="flex items-center gap-3">
                  <span className="text-sm tabular-nums text-sky-300">{sharePct}%</span>
                  <button
                    onClick={() => onRemove(h.ticker)}
                    className="grid h-6 w-6 place-items-center rounded-full text-white/40 transition hover:bg-white/10 hover:text-white/80"
                    aria-label={`Remove ${h.ticker}`}
                  >
                    ×
                  </button>
                </div>
              </div>
              <input
                type="range"
                min={0}
                max={100}
                value={Math.round(h.weight)}
                onChange={(e) => onWeightChange(h.ticker, Number(e.target.value))}
                style={{ ["--pct" as string]: `${sharePct}%` }}
                className="mt-1.5 w-full"
              />
            </motion.div>
          );
        })}
      </AnimatePresence>
    </div>
  );
}

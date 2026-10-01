import { motion } from "framer-motion";
import type { Analysis } from "../lib/api";
import { EASE, pct } from "../lib/format";

/**
 * Each holding's share of the portfolio's total exposure to the dominant
 * hidden factor (PC1). The largest share is the single point of failure.
 */
export default function Exposure({
  analysis,
  focus,
  onFocus,
}: {
  analysis: Analysis;
  focus: string | null;
  onFocus: (ticker: string | null) => void;
}) {
  const rows = Object.entries(analysis.spof.per_ticker_exposure).sort((a, b) => b[1] - a[1]);
  const max = Math.max(...rows.map(([, v]) => v), 0.0001);

  return (
    <section className="panel">
      <div className="panel-head flex-col items-start gap-0.5 sm:flex-row sm:items-baseline">
        <h2 className="panel-title">Exposure to the hidden factor</h2>
        <span className="meta">
          One factor drives <span className="num text-fg2">{Math.round(analysis.hidden_factor_pct * 100)}%</span> of daily movement
        </span>
      </div>
      <ul className="space-y-1 p-3" onMouseLeave={() => onFocus(null)}>
        {rows.map(([ticker, v]) => {
          const isSpof = ticker === analysis.spof.ticker;
          const dimmed = focus !== null && focus !== ticker;
          return (
            <motion.li
              key={ticker}
              layout="position"
              transition={{ duration: 0.4, ease: EASE }}
              onMouseEnter={() => onFocus(ticker)}
              className="grid grid-cols-[4rem_1fr_3rem] items-center gap-3 rounded-lg px-2 py-1.5 transition-opacity duration-200"
              style={{ opacity: dimmed ? 0.4 : 1 }}
            >
              <span className={`ticker text-[13px] ${isSpof ? "text-fg" : "text-fg2"}`}>{ticker}</span>
              <div className="h-1.5 overflow-hidden rounded-full bg-[rgba(178,164,255,0.06)]">
                <motion.div
                  className="h-full rounded-full"
                  style={{ background: isSpof ? "var(--bad)" : "var(--accent)", opacity: isSpof ? 1 : 0.7 }}
                  initial={false}
                  animate={{ width: `${(v / max) * 100}%` }}
                  transition={{ duration: 0.6, ease: EASE }}
                />
              </div>
              <span className="num text-right text-xs text-fg2">{pct(v)}</span>
            </motion.li>
          );
        })}
      </ul>
    </section>
  );
}

import { motion } from "framer-motion";
import type { Analysis } from "../lib/api";
import { pct } from "../lib/format";

/**
 * The single-point-of-failure callout — the sharp insight the whole product
 * exists to deliver. Big ticker, the amplification multiple, and one plain
 * sentence of consequence.
 */
export default function SpofCard({ analysis }: { analysis: Analysis }) {
  const { spof } = analysis;

  return (
    <div className="card border-fragile/20 bg-fragile/[0.04]">
      <div className="label text-fragile/70">Single point of failure</div>

      <div className="mt-2 flex items-end justify-between gap-4">
        <motion.div
          key={spof.ticker}
          initial={{ opacity: 0, scale: 0.9 }}
          animate={{ opacity: 1, scale: 1 }}
          transition={{ type: "spring", stiffness: 300, damping: 20 }}
          className="text-5xl font-extrabold text-white"
        >
          {spof.ticker}
        </motion.div>
        <div className="text-right">
          <motion.div
            key={spof.amplification.toFixed(1)}
            initial={{ opacity: 0, y: 6 }}
            animate={{ opacity: 1, y: 0 }}
            className="text-3xl font-extrabold text-fragile"
          >
            {spof.amplification.toFixed(1)}×
          </motion.div>
          <div className="text-xs text-white/50">worse than its weight</div>
        </div>
      </div>

      <p className="mt-4 text-sm leading-relaxed text-white/70">
        If <span className="font-semibold text-white">{spof.ticker}</span> fell{" "}
        {pct(spof.shock)}, your portfolio would drop about{" "}
        <span className="font-semibold text-fragile">{pct(Math.abs(spof.real_loss))}</span> — not the{" "}
        {pct(Math.abs(spof.naive_loss))} its size alone suggests, because its correlated holdings
        fall alongside it.
      </p>
    </div>
  );
}

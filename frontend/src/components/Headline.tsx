import { AnimatePresence, motion } from "framer-motion";
import type { Analysis } from "../lib/api";
import { EASE, pct, verdictColor, verdictLabel } from "../lib/format";
import Count from "./Count";

const BANDS = [
  { from: 0, to: 30, color: "var(--ok)" },
  { from: 30, to: 60, color: "var(--warn)" },
  { from: 60, to: 100, color: "var(--bad)" },
];

/**
 * The answer, up front: the fragility score on a banded 0–100 scale beside
 * the single point of failure and what a crash in it would actually cost.
 */
export default function Headline({ analysis, loading }: { analysis: Analysis | null; loading: boolean }) {
  return (
    <section
      aria-busy={loading}
      className="panel relative grid overflow-hidden md:grid-cols-[1.15fr_1fr]"
    >
      <LoadingLine active={loading} />
      <Score analysis={analysis} />
      <div className="border-t border-line md:border-l md:border-t-0">
        <Spof analysis={analysis} />
      </div>
    </section>
  );
}

function LoadingLine({ active }: { active: boolean }) {
  return (
    <AnimatePresence>
      {active && (
        <motion.div
          className="pointer-events-none absolute inset-x-0 top-0 h-px overflow-hidden"
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          exit={{ opacity: 0, transition: { duration: 0.3 } }}
        >
          <motion.div
            className="h-full w-1/3 bg-gradient-to-r from-transparent via-[var(--accent)] to-transparent"
            animate={{ x: ["-100%", "300%"] }}
            transition={{ duration: 1.1, ease: "easeInOut", repeat: Infinity }}
          />
        </motion.div>
      )}
    </AnimatePresence>
  );
}

function Score({ analysis }: { analysis: Analysis | null }) {
  const score = analysis?.score ?? 0;
  const verdict = analysis?.verdict;
  const color = verdict ? verdictColor[verdict] : "var(--fg-3)";

  return (
    <div className="flex flex-col justify-between gap-6 p-5 sm:p-6">
      <div className="flex items-center justify-between">
        <h2 className="text-[13px] font-medium text-fg2">Fragility score</h2>
        {verdict && (
          <span
            className="inline-flex items-center gap-1.5 rounded-full px-2 py-0.5 text-xs font-medium"
            style={{ color, background: `color-mix(in srgb, ${color} 12%, transparent)` }}
          >
            <span className="h-1.5 w-1.5 rounded-full" style={{ background: color }} />
            {verdictLabel[verdict]}
          </span>
        )}
      </div>

      <div className="num flex items-baseline gap-2">
        <span className="text-[64px] font-medium leading-none tracking-[-0.04em] text-fg sm:text-[76px]">
          {analysis ? <Count value={score} /> : "––"}
        </span>
        <span className="text-lg text-fg3">/ 100</span>
      </div>

      <div>
        <div className="relative h-2">
          <div className="absolute inset-0 flex gap-[3px]">
            {BANDS.map((b) => (
              <div
                key={b.from}
                className="h-full rounded-full"
                style={{
                  flex: b.to - b.from,
                  background: `color-mix(in srgb, ${b.color} ${verdict && verdictColor[verdict] === b.color ? 34 : 12}%, transparent)`,
                  transition: "background 400ms var(--ease-out)",
                }}
              />
            ))}
          </div>
          {analysis && (
            <motion.div
              className="absolute -top-1.5 h-5 w-[3px] -translate-x-1/2 rounded-full bg-fg shadow-[0_0_0_3px_var(--panel)]"
              initial={false}
              animate={{ left: `${Math.min(100, Math.max(0, score))}%` }}
              transition={{ type: "spring", stiffness: 120, damping: 18 }}
            />
          )}
        </div>
        <div className="num mt-2.5 flex text-[11px] text-fg3">
          <span style={{ flex: 30 }}>0 Resilient</span>
          <span style={{ flex: 30 }}>30 Moderate</span>
          <span style={{ flex: 40 }}>60 Fragile</span>
          <span>100</span>
        </div>
      </div>
    </div>
  );
}

function Spof({ analysis }: { analysis: Analysis | null }) {
  if (!analysis) {
    return (
      <div className="flex h-full min-h-[220px] items-center justify-center p-6 text-sm text-fg3">
        Fetching price history…
      </div>
    );
  }
  const { spof } = analysis;
  const naive = Math.abs(spof.naive_loss);
  const real = Math.abs(spof.real_loss);
  const scale = Math.max(real, naive, 0.0001);

  return (
    <div className="flex h-full flex-col gap-5 p-5 sm:p-6">
      <h2 className="text-[13px] font-medium text-fg2">Single point of failure</h2>

      <div className="flex items-end justify-between gap-4">
        <AnimatePresence mode="popLayout" initial={false}>
          <motion.div
            key={spof.ticker}
            initial={{ opacity: 0, y: 8, filter: "blur(4px)" }}
            animate={{ opacity: 1, y: 0, filter: "blur(0px)" }}
            exit={{ opacity: 0, y: -8, filter: "blur(4px)" }}
            transition={{ duration: 0.35, ease: EASE }}
            className="ticker text-[40px] font-medium leading-none tracking-[-0.03em] text-fg"
          >
            {spof.ticker}
          </motion.div>
        </AnimatePresence>
        <div className="text-right">
          <div className="num text-2xl font-medium leading-none text-bad">
            <Count value={spof.amplification} digits={1} suffix="×" />
          </div>
          <div className="meta mt-1.5">worse than its weight implies</div>
        </div>
      </div>

      <div className="space-y-2.5">
        <LossBar label="By weight alone" value={naive} scale={scale} color="var(--fg-3)" />
        <LossBar label="With correlated holdings" value={real} scale={scale} color="var(--bad)" />
      </div>

      <p className="text-[13px] leading-relaxed text-fg2">
        If <span className="font-medium text-fg">{spof.ticker}</span> fell {pct(spof.shock)}, the
        holdings that move with it fall too, so the portfolio loses about{" "}
        <span className="num text-fg">{pct(real, 1)}</span>.
      </p>
    </div>
  );
}

function LossBar({ label, value, scale, color }: { label: string; value: number; scale: number; color: string }) {
  return (
    <div className="grid grid-cols-[1fr_auto] items-center gap-x-3 gap-y-1">
      <span className="text-xs text-fg2">{label}</span>
      <span className="num text-xs text-fg">−{pct(value, 1)}</span>
      <div className="col-span-2 h-1.5 overflow-hidden rounded-full bg-[rgba(178,164,255,0.07)]">
        <motion.div
          className="h-full rounded-full"
          style={{ background: color }}
          initial={false}
          animate={{ width: `${(value / scale) * 100}%` }}
          transition={{ duration: 0.6, ease: EASE }}
        />
      </div>
    </div>
  );
}

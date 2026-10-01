import { motion } from "framer-motion";
import type { Analysis } from "../lib/api";
import { EASE, metricLabel } from "../lib/format";

const BRANCHES: { key: keyof Analysis["branches"]; label: string; hint: string; tone: number }[] = [
  { key: "co_movement", label: "Co-movement", hint: "Holdings that rise and fall together", tone: 1 },
  { key: "tail_risk", label: "Tail risk", hint: "How bad the bad days get", tone: 0.62 },
  { key: "position_sizing", label: "Position sizing", hint: "How evenly the money is split", tone: 0.36 },
];

/**
 * The score is a weighted blend of three branches. One stacked bar shows how
 * many points each contributes; the rows show the arithmetic and the metrics
 * inside each branch.
 */
export default function Composition({ analysis }: { analysis: Analysis }) {
  const parts = BRANCHES.map((b) => {
    const branch = analysis.branches[b.key];
    return { ...b, branch, points: branch.score * branch.weight };
  });

  return (
    <section className="panel">
      <div className="panel-head">
        <h2 className="panel-title">How the score is built</h2>
        <span className="meta hidden sm:inline">Branch score × weight</span>
      </div>

      <div className="p-5">
        <div className="flex h-2.5 gap-[3px] overflow-hidden rounded-full bg-[rgba(178,164,255,0.06)]">
          {parts.map((p) => (
            <motion.div
              key={p.key}
              className="h-full first:rounded-l-full"
              style={{ background: `color-mix(in srgb, var(--accent) ${p.tone * 100}%, transparent)` }}
              initial={false}
              animate={{ width: `${p.points}%` }}
              transition={{ duration: 0.6, ease: EASE }}
            />
          ))}
        </div>

        <ul className="mt-5 divide-y divide-[var(--line)]">
          {parts.map((p) => (
            <li key={p.key} className="grid grid-cols-[auto_1fr_auto] gap-x-3 py-3 first:pt-0 last:pb-0">
              <span
                className="mt-1.5 h-2 w-2 rounded-sm"
                style={{ background: `color-mix(in srgb, var(--accent) ${p.tone * 100}%, transparent)` }}
              />
              <div className="min-w-0">
                <div className="text-[13px] font-medium text-fg">{p.label}</div>
                <div className="meta mt-0.5">{p.hint}</div>
                <div className="mt-2 flex flex-wrap gap-x-4 gap-y-1">
                  {Object.entries(p.branch.metrics).map(([k, v]) => (
                    <span key={k} className="text-xs text-fg2">
                      {metricLabel[k] ?? k} <span className="num text-fg">{v.toFixed(0)}</span>
                    </span>
                  ))}
                </div>
              </div>
              <div className="num text-right text-xs text-fg3">
                <span className="text-fg2">{p.branch.score.toFixed(0)}</span> ×{" "}
                {Math.round(p.branch.weight * 100)}%
                <div className="mt-0.5 text-[15px] text-fg">{p.points.toFixed(1)}</div>
              </div>
            </li>
          ))}
        </ul>
      </div>
    </section>
  );
}

import { motion } from "framer-motion";
import type { Analysis } from "../lib/api";

const BRANCH_META: { key: keyof Analysis["branches"]; label: string; hint: string }[] = [
  { key: "co_movement", label: "Co-movement", hint: "hidden shared risk" },
  { key: "tail_risk", label: "Tail risk", hint: "how bad a bad day gets" },
  { key: "position_sizing", label: "Position sizing", hint: "how evenly split" },
];

/**
 * The three risk branches (A / B / C from the model) as animated bars, each
 * labeled with its weight in the final blend. Makes the composite score
 * legible: you can see which branch is driving it.
 */
export default function BranchBars({ analysis }: { analysis: Analysis }) {
  return (
    <div className="card">
      <div className="label mb-4">The three branches</div>
      <div className="space-y-4">
        {BRANCH_META.map(({ key, label, hint }) => {
          const branch = analysis.branches[key];
          const val = branch.score;
          return (
            <div key={key}>
              <div className="mb-1 flex items-baseline justify-between">
                <span className="text-sm font-semibold text-white/85">
                  {label}{" "}
                  <span className="text-xs font-normal text-white/40">· {hint}</span>
                </span>
                <span className="text-sm tabular-nums text-white/70">
                  {val.toFixed(0)}
                  <span className="ml-2 text-[10px] text-white/35">
                    {Math.round(branch.weight * 100)}% weight
                  </span>
                </span>
              </div>
              <div className="h-2.5 w-full overflow-hidden rounded-full bg-white/[0.06]">
                <motion.div
                  className="h-full rounded-full"
                  style={{
                    background:
                      "linear-gradient(90deg, #38a5ff 0%, #8fd0ff 100%)",
                  }}
                  initial={{ width: 0 }}
                  animate={{ width: `${Math.min(100, val)}%` }}
                  transition={{ duration: 0.7, ease: [0.22, 1, 0.36, 1] }}
                />
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}

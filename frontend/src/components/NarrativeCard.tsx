import { motion } from "framer-motion";
import type { Analysis } from "../lib/api";

/**
 * The plain-English overview — a deterministic, template-generated summary of
 * the current portfolio's fragility.
 */
export default function NarrativeCard({ analysis }: { analysis: Analysis }) {
  return (
    <div className="card border-l-2 border-l-sky-500/60">
      <div className="label text-sky-300/70">Overview</div>

      <motion.p
        key={analysis.narrative}
        initial={{ opacity: 0, y: 6 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.4 }}
        className="mt-3 text-[14px] leading-relaxed text-white/85"
      >
        {analysis.narrative || analysis.attribution}
      </motion.p>
    </div>
  );
}

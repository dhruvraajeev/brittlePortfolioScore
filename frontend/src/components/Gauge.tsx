import { motion, useMotionValue, useTransform, animate } from "framer-motion";
import { useEffect, useState } from "react";
import type { Verdict } from "../lib/api";
import { verdictColor, verdictLabel } from "../lib/format";

/**
 * The hero: a 270° radial gauge. The arc sweeps to the score and the number
 * counts up, both spring-animated so every slider nudge reads as cause →
 * effect. The color tracks the verdict band.
 */
export default function Gauge({ score, verdict }: { score: number; verdict: Verdict }) {
  const size = 220;
  const stroke = 16;
  const radius = (size - stroke) / 2;
  const cx = size / 2;
  const cy = size / 2;

  // 270° arc, rotated so the gap sits at the bottom.
  const START = 135;
  const SWEEP = 270;
  const circumference = 2 * Math.PI * radius;
  const arcLength = (SWEEP / 360) * circumference;

  const color = verdictColor[verdict];

  // Animate the displayed number for a lively count-up when the score
  // changes. `display` is seeded with the real score so it's never blank
  // (even before the animation's first frame) — the animation runs from the
  // previous value to the new one on every change.
  const mv = useMotionValue(score);
  const rounded = useTransform(mv, (v) => Math.round(v));
  const [display, setDisplay] = useState(Math.round(score));

  useEffect(() => {
    const controls = animate(mv, score, {
      duration: 0.9,
      ease: [0.22, 1, 0.36, 1],
    });
    const unsub = rounded.on("change", (v) => setDisplay(v));
    return () => {
      controls.stop();
      unsub();
    };
  }, [score, mv, rounded]);

  const progress = Math.max(0, Math.min(100, score)) / 100;

  return (
    <div className="relative flex flex-col items-center">
      <svg width={size} height={size} className="overflow-visible">
        <defs>
          <linearGradient id="gaugeGrad" x1="0%" y1="0%" x2="100%" y2="100%">
            <stop offset="0%" stopColor={color} stopOpacity="0.9" />
            <stop offset="100%" stopColor="#5cb8ff" stopOpacity="0.9" />
          </linearGradient>
          <filter id="gaugeGlow">
            <feGaussianBlur stdDeviation="4" result="b" />
            <feMerge>
              <feMergeNode in="b" />
              <feMergeNode in="SourceGraphic" />
            </feMerge>
          </filter>
        </defs>

        {/* Track */}
        <circle
          cx={cx}
          cy={cy}
          r={radius}
          fill="none"
          stroke="rgba(255,255,255,0.08)"
          strokeWidth={stroke}
          strokeLinecap="round"
          strokeDasharray={`${arcLength} ${circumference}`}
          transform={`rotate(${START} ${cx} ${cy})`}
        />

        {/* Value arc */}
        <motion.circle
          cx={cx}
          cy={cy}
          r={radius}
          fill="none"
          stroke="url(#gaugeGrad)"
          strokeWidth={stroke}
          strokeLinecap="round"
          filter="url(#gaugeGlow)"
          transform={`rotate(${START} ${cx} ${cy})`}
          strokeDasharray={`${arcLength} ${circumference}`}
          initial={{ strokeDashoffset: arcLength }}
          animate={{ strokeDashoffset: arcLength * (1 - progress) }}
          transition={{ duration: 0.9, ease: [0.22, 1, 0.36, 1] }}
        />
      </svg>

      {/* Center readout */}
      <div className="absolute inset-0 flex flex-col items-center justify-center">
        <div className="label mb-1">Fragility Score</div>
        <div
          className="text-[54px] font-extrabold leading-none tabular-nums"
          style={{ color, textShadow: `0 0 30px ${color}55` }}
        >
          {display}
        </div>
        <motion.div
          key={verdict}
          initial={{ opacity: 0, y: 4 }}
          animate={{ opacity: 1, y: 0 }}
          className="chip mt-2"
          style={{ color, borderColor: `${color}55`, background: `${color}14` }}
        >
          {verdictLabel[verdict]}
        </motion.div>
      </div>
    </div>
  );
}

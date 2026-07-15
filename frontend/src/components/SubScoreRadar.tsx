import { motion } from "framer-motion";
import type { Analysis } from "../lib/api";
import { metricLabel } from "../lib/format";

/**
 * A radar of every individual sub-score (0-100). It's the "show the work"
 * panel: the gauge is one number, this is the shape of the risk beneath it.
 *
 * Hand-rolled in plain SVG (no chart library) — same approach as the gauge
 * and the particle field. The geometry is simple: each metric gets an axis
 * spoke at an even angle around the circle, and the value polygon connects
 * each metric's point at radius ∝ its 0-100 score.
 */
const SIZE = 240;
const CX = SIZE / 2;
const CY = SIZE / 2;
const R = 80; // outer radius of the 100 ring
const RINGS = [0.25, 0.5, 0.75, 1]; // grid rings as fractions of R
const ACCENT = "#5cb8ff";

export default function SubScoreRadar({ analysis }: { analysis: Analysis }) {
  const metrics = Object.entries(analysis.sub_scores);
  const n = metrics.length;

  // Angle for axis i, starting straight up and going clockwise.
  const angle = (i: number) => -Math.PI / 2 + (i * 2 * Math.PI) / n;
  const point = (i: number, frac: number): [number, number] => {
    const a = angle(i);
    return [CX + Math.cos(a) * R * frac, CY + Math.sin(a) * R * frac];
  };
  const toPath = (frac: (i: number) => number) =>
    metrics.map((_, i) => point(i, frac(i)).join(",")).join(" ");

  const valuePolygon = toPath((i) =>
    Math.max(0, Math.min(100, metrics[i][1])) / 100
  );

  return (
    <div className="card">
      <div className="label mb-1">Risk breakdown</div>
      <div className="grid place-items-center">
        <svg
          viewBox={`0 0 ${SIZE} ${SIZE}`}
          className="h-[240px] w-full max-w-[300px] overflow-visible"
        >
          {/* Grid rings */}
          {RINGS.map((frac) => (
            <polygon
              key={frac}
              points={toPath(() => frac)}
              fill="none"
              stroke="rgba(255,255,255,0.10)"
              strokeWidth={1}
            />
          ))}

          {/* Axis spokes */}
          {metrics.map((_, i) => {
            const [x, y] = point(i, 1);
            return (
              <line
                key={i}
                x1={CX}
                y1={CY}
                x2={x}
                y2={y}
                stroke="rgba(255,255,255,0.08)"
                strokeWidth={1}
              />
            );
          })}

          {/* Value polygon */}
          <motion.polygon
            key={valuePolygon}
            points={valuePolygon}
            fill={ACCENT}
            fillOpacity={0.26}
            stroke={ACCENT}
            strokeWidth={2}
            strokeLinejoin="round"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            transition={{ duration: 0.5, ease: [0.22, 1, 0.36, 1] }}
          />

          {/* Vertex dots */}
          {metrics.map(([, v], i) => {
            const [x, y] = point(i, Math.max(0, Math.min(100, v)) / 100);
            return <circle key={i} cx={x} cy={y} r={2.5} fill={ACCENT} />;
          })}

          {/* Axis labels */}
          {metrics.map(([key], i) => {
            const a = angle(i);
            const lx = CX + Math.cos(a) * (R + 14);
            const ly = CY + Math.sin(a) * (R + 14);
            const anchor =
              Math.abs(Math.cos(a)) < 0.3 ? "middle" : Math.cos(a) > 0 ? "start" : "end";
            return (
              <text
                key={key}
                x={lx}
                y={ly}
                textAnchor={anchor}
                dominantBaseline="middle"
                fontSize={11}
                fill="rgba(255,255,255,0.6)"
              >
                {metricLabel[key] ?? key}
              </text>
            );
          })}
        </svg>
      </div>
    </div>
  );
}

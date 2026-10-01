import type { Analysis } from "../lib/api";
import { pct } from "../lib/format";

/**
 * How big the swings are and how bad the worst days get: volatility and
 * drawdown, then historical VaR / CVaR at two confidence levels.
 */
export default function Tail({ analysis }: { analysis: Analysis }) {
  const { tail } = analysis;
  const rows = [
    { level: "95%", worst: "5%", var: tail.var, cvar: tail.cvar },
    { level: "99%", worst: "1%", var: tail.var_99, cvar: tail.cvar_99 },
  ];

  return (
    <section className="panel">
      <div className="panel-head">
        <h2 className="panel-title">Magnitude and tail risk</h2>
        <span className="meta hidden sm:inline">Historical, selected period</span>
      </div>

      <dl className="grid grid-cols-2 gap-px bg-[var(--line)]">
        <Stat label="Annual volatility" value={pct(tail.annual_vol, 0)} />
        <Stat label="Max drawdown" value={`−${pct(Math.abs(tail.max_drawdown), 0)}`} />
      </dl>

      <div className="border-t border-line px-5 py-4">
        <table className="num w-full text-left text-[13px]">
          <thead>
            <tr className="text-xs text-fg3">
              <th className="pb-2 font-normal">Confidence</th>
              <th className="pb-2 text-right font-normal" title="Value at Risk: the loss a day exceeds only this rarely">
                Daily VaR
              </th>
              <th className="pb-2 text-right font-normal" title="Conditional VaR: the average loss on those worst days">
                Daily CVaR
              </th>
            </tr>
          </thead>
          <tbody className="text-fg">
            {rows.map((r) => (
              <tr key={r.level} className="border-t border-line">
                <td className="py-2 text-fg2">{r.level}</td>
                <td className="py-2 text-right">−{pct(Math.abs(r.var), 1)}</td>
                <td className="py-2 text-right">−{pct(Math.abs(r.cvar), 1)}</td>
              </tr>
            ))}
          </tbody>
        </table>
        <p className="mt-3 text-xs leading-relaxed text-fg3">
          On the worst 5% of days, the portfolio lost{" "}
          <span className="text-fg2">{pct(Math.abs(tail.cvar), 1)}</span> on average. VaR is the
          line those days cross; CVaR is how far past it they go.
        </p>
      </div>
    </section>
  );
}

function Stat({ label, value }: { label: string; value: string }) {
  return (
    <div className="bg-panel px-5 py-4">
      <dt className="meta">{label}</dt>
      <dd className="num mt-1 text-xl text-fg">{value}</dd>
    </div>
  );
}

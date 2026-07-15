import { useEffect, useRef, useState } from "react";
import { motion } from "framer-motion";
import { analyze } from "./lib/api";
import type { Analysis, AnalyzeRequest } from "./lib/api";
import { pct } from "./lib/format";
import ParticleField from "./components/ParticleField";
import Gauge from "./components/Gauge";
import SpofCard from "./components/SpofCard";
import SubScoreRadar from "./components/SubScoreRadar";
import BranchBars from "./components/BranchBars";
import PortfolioPanel from "./components/PortfolioPanel";
import NarrativeCard from "./components/NarrativeCard";

export interface Holding {
  ticker: string;
  weight: number; // raw 0-100 slider value; normalized for display/scoring
}

const DEFAULT_HOLDINGS: Holding[] = [
  { ticker: "NVDA", weight: 30 },
  { ticker: "AMD", weight: 20 },
  { ticker: "AVGO", weight: 20 },
  { ticker: "JPM", weight: 15 },
  { ticker: "XOM", weight: 15 },
];

const DEBOUNCE_MS = 350;

export default function App() {
  const [holdings, setHoldings] = useState<Holding[]>(DEFAULT_HOLDINGS);
  const [period, setPeriod] = useState("1y");
  const [analysis, setAnalysis] = useState<Analysis | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const abortRef = useRef<AbortController | null>(null);

  // Debounced live analysis: any change to holdings/period recomputes after
  // a short pause, cancelling any in-flight request.
  useEffect(() => {
    if (holdings.length === 0) {
      setAnalysis(null);
      return;
    }
    const handle = setTimeout(async () => {
      abortRef.current?.abort();
      const controller = new AbortController();
      abortRef.current = controller;
      setLoading(true);
      setError(null);

      const req: AnalyzeRequest = {
        tickers: holdings.map((h) => h.ticker),
        weights: Object.fromEntries(holdings.map((h) => [h.ticker, h.weight])),
        period,
      };
      try {
        const result = await analyze(req, controller.signal);
        setAnalysis(result);
      } catch (e) {
        if ((e as Error).name === "AbortError") return;
        setError(e instanceof Error ? e.message : "Something went wrong.");
      } finally {
        setLoading(false);
      }
    }, DEBOUNCE_MS);

    return () => clearTimeout(handle);
  }, [holdings, period]);

  // ---- handlers ---------------------------------------------------------

  const addTicker = (ticker: string) => {
    setHoldings((hs) => {
      if (hs.some((h) => h.ticker === ticker)) return hs;
      const mean = hs.length ? hs.reduce((a, h) => a + h.weight, 0) / hs.length : 20;
      return [...hs, { ticker, weight: Math.round(mean) || 20 }];
    });
  };

  const removeTicker = (ticker: string) => {
    setHoldings((hs) => (hs.length > 1 ? hs.filter((h) => h.ticker !== ticker) : hs));
  };

  const changeWeight = (ticker: string, weight: number) => {
    setHoldings((hs) => hs.map((h) => (h.ticker === ticker ? { ...h, weight } : h)));
  };

  return (
    <div className="min-h-full">
      <ParticleField />

      <div className="mx-auto max-w-5xl px-5 py-10 sm:px-8">
        {/* Header */}
        <header className="mb-9">
          <motion.div
            initial={{ opacity: 0, y: -8 }}
            animate={{ opacity: 1, y: 0 }}
            className="flex items-center gap-2 text-sky-300"
          >
            <span className="h-2 w-2 animate-floaty rounded-full bg-sky-400 shadow-glow" />
            <span className="label text-sky-300/80">Brittle</span>
          </motion.div>
          <motion.h1
            initial={{ opacity: 0, y: 8 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.05 }}
            className="mt-3 max-w-2xl text-3xl font-extrabold leading-tight tracking-tight sm:text-[38px]"
          >
            Which single holding, if it crashed tomorrow, would hurt you most?
          </motion.h1>
          <p className="mt-3 max-w-xl text-sm text-white/50">
            Apply any ticker's weight and watch your score shift. The math looks past ticker
            labels to the risk you can't see. A higher score indicates a more fragile portfolio.
          </p>
        </header>

        {error && (
          <div className="mb-6 rounded-2xl border border-fragile/30 bg-fragile/10 px-4 py-3 text-sm text-fragile">
            {error}
          </div>
        )}

        <div className="grid grid-cols-1 gap-6 lg:grid-cols-12">
          {/* Left: controls */}
          <div className="space-y-6 lg:col-span-4">
            <PortfolioPanel
              holdings={holdings}
              period={period}
              spofTicker={analysis?.spof.ticker}
              loading={loading}
              onAdd={addTicker}
              onRemove={removeTicker}
              onWeightChange={changeWeight}
              onPeriodChange={setPeriod}
            />
            {analysis && <BranchBars analysis={analysis} />}
          </div>

          {/* Right: results */}
          <div className="space-y-6 lg:col-span-8">
            {analysis ? (
              <>
                <div className="grid grid-cols-1 gap-6 md:grid-cols-2">
                  <div className="card flex items-center justify-center py-6">
                    <Gauge score={analysis.score} verdict={analysis.verdict} />
                  </div>
                  <SpofCard analysis={analysis} />
                </div>

                <NarrativeCard analysis={analysis} />

                <div className="grid grid-cols-1 gap-6 md:grid-cols-2">
                  <SubScoreRadar analysis={analysis} />
                  <TailStats analysis={analysis} />
                </div>
              </>
            ) : (
              <div className="card grid h-[400px] place-items-center text-white/40">
                {loading ? "Crunching the numbers…" : "Add a holding to begin."}
              </div>
            )}
          </div>
        </div>

        <footer className="mt-12 text-center text-xs text-white/30">
          Educational tool · not investment advice · prices via Yahoo Finance
        </footer>
      </div>
    </div>
  );
}

function TailStats({ analysis }: { analysis: Analysis }) {
  const { tail } = analysis;
  const stats = [
    { label: "Annual volatility", value: pct(tail.annual_vol, 0) },
    { label: "Max drawdown", value: pct(Math.abs(tail.max_drawdown), 0) },
    { label: "95% daily VaR", value: pct(Math.abs(tail.var), 1) },
    { label: "95% daily CVaR", value: pct(Math.abs(tail.cvar), 1) },
  ];
  return (
    <div className="card">
      <div className="label mb-4">Magnitude & tail risk</div>
      <div className="grid grid-cols-2 gap-4">
        {stats.map((s) => (
          <div key={s.label}>
            <div className="text-2xl font-bold tabular-nums text-white">{s.value}</div>
            <div className="mt-0.5 text-xs text-white/45">{s.label}</div>
          </div>
        ))}
      </div>
    </div>
  );
}

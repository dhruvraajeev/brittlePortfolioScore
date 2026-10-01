import { useEffect, useRef, useState } from "react";
import { AnimatePresence, MotionConfig, motion } from "framer-motion";
import { analyze } from "./lib/api";
import type { Analysis, AnalyzeRequest } from "./lib/api";
import { EASE } from "./lib/format";
import Headline from "./components/Headline";
import Holdings from "./components/Holdings";
import Exposure from "./components/Exposure";
import Composition from "./components/Composition";
import Tail from "./components/Tail";
import { Mark } from "./components/Icons";

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
  const [focus, setFocus] = useState<string | null>(null);

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
    <MotionConfig reducedMotion="user">
      <div className="min-h-full">
        <header className="sticky top-0 z-10 border-b border-line bg-[rgba(11,10,15,0.82)] backdrop-blur-md">
          <div className="mx-auto flex h-14 max-w-6xl items-center justify-between gap-4 px-4 sm:px-6">
            <div className="flex items-center gap-2.5">
              <Mark className="h-5 w-5" />
              <span className="text-[15px] font-semibold tracking-[-0.01em]">Brittle</span>
            </div>
            <div className="flex items-center gap-4">
              <Status loading={loading} />
              <PeriodPicker value={period} onChange={setPeriod} />
            </div>
          </div>
        </header>

        <main className="mx-auto max-w-6xl px-4 pb-16 pt-10 sm:px-6 sm:pt-14">
          <div>
            <h1 className="max-w-2xl text-balance text-[26px] font-medium leading-[1.2] tracking-[-0.025em] text-fg sm:text-[32px]">
              Which single holding, if it crashed tomorrow, would hurt you most?
            </h1>
            <p className="mt-3 text-[15px] leading-relaxed text-fg2">
              Drag any weight to see how the shared risk beneath your tickers shifts.
            </p>
          </div>

          <AnimatePresence>
            {error && (
              <motion.div
                role="alert"
                initial={{ opacity: 0, height: 0 }}
                animate={{ opacity: 1, height: "auto" }}
                exit={{ opacity: 0, height: 0 }}
                transition={{ duration: 0.3, ease: EASE }}
                className="overflow-hidden"
              >
                <div className="mt-6 rounded-lg border border-[color-mix(in_srgb,var(--bad)_30%,transparent)] bg-[color-mix(in_srgb,var(--bad)_8%,transparent)] px-4 py-3 text-[13px] text-bad">
                  {error}
                </div>
              </motion.div>
            )}
          </AnimatePresence>

          <div className="mt-8">
            <Headline analysis={analysis} loading={loading} />
          </div>

          <div className="mt-6 grid grid-cols-1 gap-4 lg:grid-cols-12">
            <div className="lg:col-span-5">
              <div className="lg:sticky lg:top-20">
                <Holdings
                  holdings={holdings}
                  spofTicker={analysis?.spof.ticker}
                  focus={focus}
                  onFocus={setFocus}
                  onAdd={addTicker}
                  onRemove={removeTicker}
                  onWeightChange={changeWeight}
                />
              </div>
            </div>
            <div className="space-y-4 lg:col-span-7">
              {analysis && (
                <>
                  <Exposure analysis={analysis} focus={focus} onFocus={setFocus} />
                  <Composition analysis={analysis} />
                  <Tail analysis={analysis} />
                </>
              )}
            </div>
          </div>
        </main>

        <footer className="border-t border-line">
          <div className="mx-auto max-w-6xl px-4 py-6 text-xs text-fg3 sm:px-6">
            Educational tool, not investment advice. Prices via Yahoo Finance.
          </div>
        </footer>
      </div>
    </MotionConfig>
  );
}

function Status({ loading }: { loading: boolean }) {
  return (
    <span className="flex items-center gap-2 text-xs text-fg3" aria-live="polite">
      <span className="relative flex h-1.5 w-1.5">
        <span
          className={`absolute inset-0 rounded-full ${loading ? "animate-pulse bg-accent" : "bg-ok"}`}
        />
      </span>
      <span className="sr-only sm:not-sr-only">{loading ? "Updating" : "Live"}</span>
    </span>
  );
}

const PERIODS = ["6mo", "1y", "2y", "5y"];

function PeriodPicker({ value, onChange }: { value: string; onChange: (p: string) => void }) {
  return (
    <div role="radiogroup" aria-label="History window" className="flex rounded-lg border border-line bg-panel p-0.5">
      {PERIODS.map((p) => {
        const active = p === value;
        return (
          <button
            key={p}
            role="radio"
            aria-checked={active}
            onClick={() => onChange(p)}
            className={`num relative rounded-md px-2.5 py-1 text-xs transition-colors ${
              active ? "text-fg" : "text-fg3 hover:text-fg2"
            }`}
          >
            {active && (
              <motion.span
                layoutId="period-pill"
                className="absolute inset-0 rounded-md bg-raised shadow-[inset_0_0_0_1px_var(--line-strong)]"
                transition={{ type: "spring", stiffness: 500, damping: 38 }}
              />
            )}
            <span className="relative">{p}</span>
          </button>
        );
      })}
    </div>
  );
}

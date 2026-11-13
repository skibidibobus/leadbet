"use client";

import React, { useEffect, useMemo, useState } from "react";
import {
  ACTIVE_V1_SPORTS,
  CalibrationMetricsResponse,
  fetchCalibrationMetrics,
} from "../../lib/api";

const TIME_HORIZONS = [
  { value: "30d", label: "Ostatnie 30 dni" },
  { value: "90d", label: "Ostatnie 90 dni" },
  { value: "365d", label: "Pełny sezon (365 dni)" },
] as const;

export default function KalibracjaPage() {
  const [timeHorizon, setTimeHorizon] = useState<string>("90d");
  const [metrics, setMetrics] = useState<CalibrationMetricsResponse | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let mounted = true;
    async function load() {
      setLoading(true);
      setError(null);
      try {
        const res = await fetchCalibrationMetrics(timeHorizon);
        if (mounted) setMetrics(res);
      } catch (err) {
        if (mounted) {
          setError(
            err instanceof Error
              ? err.message
              : "Nie udało się pobrać metryk kalibracji."
          );
        }
      } finally {
        if (mounted) setLoading(false);
      }
    }
    load();
    return () => {
      mounted = false;
    };
  }, [timeHorizon]);

  const activeSportsBreakdown = useMemo(() => {
    if (!metrics) return [];
    const allowed = new Set<string>(ACTIVE_V1_SPORTS.map((s) => s.slug));
    return metrics.by_sport.filter((item) => allowed.has(item.sport));
  }, [metrics]);

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 space-y-8">
      {/* Header */}
      <section className="rounded-xl border border-border-hairline bg-surface-slate p-6 flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div className="space-y-1.5">
          <div className="inline-flex items-center gap-2 px-2.5 py-0.5 rounded bg-canvas-midnight border border-border-hairline text-xs font-mono text-signal-emerald">
            AUDYT STATYSTYCZNY PROGNOZ • BRIER &amp; CLV
          </div>
          <h1 className="text-2xl sm:text-3xl font-extrabold text-text-primary tracking-tight">
            Kalibracja Modeli Probabilistycznych i Audyt CLV
          </h1>
          <p className="text-xs sm:text-sm text-text-secondary max-w-3xl">
            Weryfikacja zgodności przewidywanych prawdopodobieństw z rzeczywistą częstością
            trafień (Reliability Diagram) oraz przewagi nad kursem zamknięcia Pinnacle (Closing Line Value).
          </p>
        </div>

        <div className="flex items-center gap-2 shrink-0">
          {TIME_HORIZONS.map((th) => (
            <button
              key={th.value}
              type="button"
              onClick={() => setTimeHorizon(th.value)}
              className={`px-3 py-1.5 rounded-lg text-xs font-mono font-semibold border transition-colors ${
                timeHorizon === th.value
                  ? "bg-signal-emerald text-canvas-obsidian border-signal-emerald"
                  : "bg-canvas-midnight text-text-secondary border-border-hairline hover:bg-surface-elevated"
              }`}
            >
              {th.label}
            </button>
          ))}
        </div>
      </section>

      {error && (
        <div className="rounded-lg border border-semantic-loss/40 bg-semantic-loss/10 p-4 text-xs font-mono text-semantic-loss">
          ▼ Błąd: {error}
        </div>
      )}

      {loading || !metrics ? (
        <div className="rounded-xl border border-border-hairline bg-surface-slate p-10 text-center text-sm font-mono text-text-muted">
          Obliczanie Brier Score, Log-Loss i przedziałów kalibracji...
        </div>
      ) : (
        <>
          {/* KPI Cards: Brier, BSS, LogLoss, CLV Beat Rate, Avg CLV */}
          <section className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-5 gap-4 font-mono tabular-nums">
            <div className="rounded-xl border border-border-hairline bg-surface-slate p-4 space-y-1">
              <div className="text-[11px] text-text-muted">BRIER SCORE (NIŻSZY = LEPSZY)</div>
              <div className="text-2xl font-extrabold text-signal-emerald">
                {metrics.overall.brier_score.toFixed(4)}
              </div>
              <div className="text-[11px] font-sans text-text-secondary">
                Próba: {metrics.overall.sample_size} rozliczonych meczów
              </div>
            </div>

            <div className="rounded-xl border border-border-hairline bg-surface-slate p-4 space-y-1">
              <div className="text-[11px] text-text-muted">BRIER SKILL SCORE (BSS)</div>
              <div className="text-2xl font-extrabold text-signal-emerald">
                ▲ +{(metrics.overall.brier_skill_score * 100).toFixed(2)}%
              </div>
              <div className="text-[11px] font-sans text-text-secondary">
                Przewaga nad modelem referencyjnym
              </div>
            </div>

            <div className="rounded-xl border border-border-hairline bg-surface-slate p-4 space-y-1">
              <div className="text-[11px] text-text-muted">LOG-LOSS (ENTROPIA KRZYŻOWA)</div>
              <div className="text-2xl font-extrabold text-text-primary">
                {metrics.overall.log_loss.toFixed(4)}
              </div>
              <div className="text-[11px] font-sans text-text-secondary">
                Ścisła funkcja oceny ostrości rozkładu
              </div>
            </div>

            <div className="rounded-xl border border-border-hairline bg-surface-slate p-4 space-y-1">
              <div className="text-[11px] text-text-muted">CLV BEAT RATE (PINNACLE)</div>
              <div className="text-2xl font-extrabold text-signal-emerald">
                ▲ {(metrics.overall.clv_beat_rate * 100).toFixed(1)}%
              </div>
              <div className="text-[11px] font-sans text-text-secondary">
                Odsetek pobić kursu zamknięcia
              </div>
            </div>

            <div className="rounded-xl border border-border-hairline bg-surface-slate p-4 space-y-1">
              <div className="text-[11px] text-text-muted">ŚREDNIE CLV NETTO</div>
              <div className="text-2xl font-extrabold text-alpha-amber">
                ▲ +{(metrics.overall.avg_clv_percentage * 100).toFixed(2)}%
              </div>
              <div className="text-[11px] font-sans text-text-secondary">
                Średnia przewaga nad linią zamykającą
              </div>
            </div>
          </section>

          {/* Reliability Diagram SVG + Bins Table */}
          <div className="grid grid-cols-1 lg:grid-cols-12 gap-6 items-start">
            {/* Clean SVG Reliability Diagram */}
            <section className="lg:col-span-7 rounded-xl border border-border-hairline bg-surface-slate p-6 space-y-4">
              <div className="flex flex-wrap items-center justify-between gap-2 border-b border-border-hairline pb-3">
                <div>
                  <h2 className="text-base font-bold text-text-primary">
                    Krzywa Kalibracji Modelu (Reliability Diagram)
                  </h2>
                  <p className="text-xs text-text-muted">
                    Oś X: Prognozowane prawdopodobieństwo p_model • Oś Y: Empiryczna częstość wygranych
                  </p>
                </div>
                <div className="flex items-center gap-4 text-xs font-mono">
                  <span className="flex items-center gap-1.5 text-text-muted">
                    <span className="w-4 border-t border-dashed border-text-muted inline-block" />
                    Idealna kalibracja (y = x)
                  </span>
                  <span className="flex items-center gap-1.5 text-signal-emerald">
                    <span className="w-3 h-3 rounded-full bg-signal-emerald inline-block" />
                    Empiryczna krzywa LeadBet
                  </span>
                </div>
              </div>

              <div className="w-full overflow-x-auto">
                <svg
                  viewBox="0 0 560 360"
                  className="w-full h-auto bg-canvas-midnight rounded-lg border border-border-hairline p-2"
                  role="img"
                  aria-label="Wykres kalibracji Reliability Diagram"
                >
                  {/* Axes & Grid */}
                  {[0, 0.2, 0.4, 0.6, 0.8, 1.0].map((v) => {
                    const x = 60 + v * 450;
                    const y = 310 - v * 270;
                    return (
                      <g key={v}>
                        <line
                          x1="60"
                          y1={y}
                          x2="510"
                          y2={y}
                          stroke="#23324D"
                          strokeDasharray={v === 0 ? undefined : "3 3"}
                          strokeWidth="1"
                        />
                        <line
                          x1={x}
                          y1="40"
                          x2={x}
                          y2="310"
                          stroke="#23324D"
                          strokeDasharray={v === 0 ? undefined : "3 3"}
                          strokeWidth="1"
                        />
                        <text
                          x="50"
                          y={y + 4}
                          textAnchor="end"
                          fill="#94A3B8"
                          fontSize="10"
                          fontFamily="monospace"
                        >
                          {Math.round(v * 100)}%
                        </text>
                        <text
                          x={x}
                          y="328"
                          textAnchor="middle"
                          fill="#94A3B8"
                          fontSize="10"
                          fontFamily="monospace"
                        >
                          {Math.round(v * 100)}%
                        </text>
                      </g>
                    );
                  })}

                  {/* Ideal diagonal y = x */}
                  <line
                    x1="60"
                    y1="310"
                    x2="510"
                    y2="40"
                    stroke="#94A3B8"
                    strokeWidth="1.5"
                    strokeDasharray="6 4"
                  />

                  {/* Empirical polyline connecting bins */}
                  {metrics.reliability_bins.length > 1 && (
                    <polyline
                      fill="none"
                      stroke="#10B981"
                      strokeWidth="2.5"
                      points={metrics.reliability_bins
                        .map((b) => {
                          const cx = 60 + b.mean_predicted_prob * 450;
                          const cy = 310 - b.empirical_win_rate * 270;
                          return `${cx},${cy}`;
                        })
                        .join(" ")}
                    />
                  )}

                  {/* Data points per bin */}
                  {metrics.reliability_bins.map((b) => {
                    const cx = 60 + b.mean_predicted_prob * 450;
                    const cy = 310 - b.empirical_win_rate * 270;
                    return (
                      <g key={b.bin_index}>
                        <circle
                          cx={cx}
                          cy={cy}
                          r="5"
                          fill="#10B981"
                          stroke="#0B0F19"
                          strokeWidth="2"
                        />
                        <text
                          x={cx}
                          y={cy - 10}
                          textAnchor="middle"
                          fill="#F8FAFC"
                          fontSize="9"
                          fontFamily="monospace"
                        >
                          {(b.empirical_win_rate * 100).toFixed(1)}% (n={b.sample_count})
                        </text>
                      </g>
                    );
                  })}
                </svg>
              </div>
            </section>

            {/* Reliability Bins Table */}
            <section className="lg:col-span-5 rounded-xl border border-border-hairline bg-surface-slate p-6 space-y-4">
              <div className="border-b border-border-hairline pb-3">
                <h2 className="text-base font-bold text-text-primary">
                  Rozkład Koszyków Kalibracyjnych (Bins)
                </h2>
                <p className="text-xs text-text-muted">
                  Odchylenie pomiędzy średnią prognozą a wynikiem empirycznym
                </p>
              </div>

              <div className="overflow-x-auto rounded-lg border border-border-hairline bg-canvas-midnight">
                <table className="w-full text-left border-collapse text-xs font-mono tabular-nums">
                  <thead>
                    <tr className="border-b border-border-hairline text-text-muted bg-surface-elevated/40">
                      <th className="py-2 px-2.5">Przedział</th>
                      <th className="py-2 px-2.5 text-right">Śr. P(prog)</th>
                      <th className="py-2 px-2.5 text-right">Trafienia %</th>
                      <th className="py-2 px-2.5 text-right">Próba (n)</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-border-hairline">
                    {metrics.reliability_bins.map((bin) => (
                      <tr key={bin.bin_index} className="hover:bg-surface-elevated/30">
                        <td className="py-2 px-2.5 text-text-secondary">
                          {(bin.predicted_prob_lower * 100).toFixed(0)}%–
                          {(bin.predicted_prob_upper * 100).toFixed(0)}%
                        </td>
                        <td className="py-2 px-2.5 text-right text-text-primary">
                          {(bin.mean_predicted_prob * 100).toFixed(1)}%
                        </td>
                        <td className="py-2 px-2.5 text-right font-bold text-signal-emerald">
                          {(bin.empirical_win_rate * 100).toFixed(1)}%
                        </td>
                        <td className="py-2 px-2.5 text-right text-text-muted">
                          {bin.sample_count}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </section>
          </div>

          {/* Per-Sport Breakdown (Strictly 4 active sports in v1) */}
          <section className="rounded-xl border border-border-hairline bg-surface-slate p-6 space-y-4">
            <div>
              <h2 className="text-base font-bold text-text-primary">
                Audyt Kalibracji i CLV w Podziale na Dyscypliny (4 Aktywne w v1)
              </h2>
              <p className="text-xs text-text-muted">
                Porównanie dokładności modeli dla Piłki nożnej, Koszykówki, Tenisa i Hokeja.
              </p>
            </div>

            <div className="overflow-x-auto rounded-lg border border-border-hairline bg-canvas-midnight">
              <table className="w-full text-left border-collapse text-xs font-mono tabular-nums">
                <thead>
                  <tr className="border-b border-border-hairline text-text-muted bg-surface-elevated/40">
                    <th className="py-3 px-4 font-sans">Dyscyplina</th>
                    <th className="py-3 px-4">Algorytm Modelu</th>
                    <th className="py-3 px-4 text-right">Próba (n)</th>
                    <th className="py-3 px-4 text-right">Brier Score</th>
                    <th className="py-3 px-4 text-right">Log-Loss</th>
                    <th className="py-3 px-4 text-right text-signal-emerald">
                      CLV Beat Rate
                    </th>
                    <th className="py-3 px-4 text-right text-alpha-amber">
                      Średnie CLV %
                    </th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-border-hairline">
                  {activeSportsBreakdown.map((sp) => (
                    <tr key={sp.sport} className="hover:bg-surface-elevated/30">
                      <td className="py-3 px-4 font-sans font-bold text-text-primary">
                        {sp.sport_name_pl}
                      </td>
                      <td className="py-3 px-4 text-text-secondary">{sp.model_name}</td>
                      <td className="py-3 px-4 text-right text-text-secondary">
                        {sp.sample_size}
                      </td>
                      <td className="py-3 px-4 text-right font-bold text-text-primary">
                        {sp.brier_score.toFixed(4)}
                      </td>
                      <td className="py-3 px-4 text-right text-text-secondary">
                        {sp.log_loss.toFixed(4)}
                      </td>
                      <td className="py-3 px-4 text-right font-bold text-signal-emerald">
                        ▲ {(sp.clv_beat_rate * 100).toFixed(1)}%
                      </td>
                      <td className="py-3 px-4 text-right font-bold text-alpha-amber">
                        +{(sp.avg_clv_percentage * 100).toFixed(2)}%
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </section>
        </>
      )}
    </div>
  );
}

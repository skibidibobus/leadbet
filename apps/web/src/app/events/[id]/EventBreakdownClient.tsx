"use client";

import React, { useEffect, useState } from "react";
import Link from "next/link";
import { useParams } from "next/navigation";
import {
  EventBreakdownResponse,
  fetchEventBreakdown,
} from "../../../lib/api";

function formatPct(val: number, digits = 1): string {
  return `${(val * 100).toFixed(digits)}%`;
}

function formatEv(ev: number): { text: string; isPositive: boolean } {
  const pct = (ev * 100).toFixed(2);
  if (ev >= 0) {
    return { text: `▲ +${pct}%`, isPositive: true };
  }
  return { text: `▼ ${pct}%`, isPositive: false };
}

export default function EventBreakdownPage() {
  const params = useParams<{ id: string }>();
  const eventId = params?.id || "ev_fb_ars_che";

  const [breakdown, setBreakdown] = useState<EventBreakdownResponse | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let mounted = true;
    async function load() {
      setLoading(true);
      setError(null);
      try {
        const res = await fetchEventBreakdown(eventId);
        if (mounted) setBreakdown(res);
      } catch (err) {
        if (mounted) {
          setError(
            err instanceof Error
              ? err.message
              : "Nie udało się pobrać dekompozycji zdarzenia."
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
  }, [eventId]);

  if (loading) {
    return (
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-12">
        <div className="rounded-xl border border-border-hairline bg-surface-slate p-10 text-center font-mono text-sm text-text-muted">
          Obliczanie dekompozycji modelu i fuzji bayesowskiej dla zdarzenia {eventId}...
        </div>
      </div>
    );
  }

  if (error || !breakdown) {
    return (
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-12 space-y-4">
        <Link
          href="/"
          className="inline-flex items-center gap-2 text-xs font-mono text-signal-emerald hover:underline"
        >
          ← Powrót do Pulpitu
        </Link>
        <div className="rounded-xl border border-semantic-loss/40 bg-semantic-loss/10 p-6 text-sm text-semantic-loss font-mono">
          ▼ Błąd: {error || "Nie znaleziono zdarzenia."}
        </div>
      </div>
    );
  }

  const primaryMarket = breakdown.available_markets[0];
  const homeRatings = breakdown.competitor_ratings.home || {};
  const awayRatings = breakdown.competitor_ratings.away || {};
  const homeElo = Number(homeRatings.rating_elo ?? 1500);
  const awayElo = Number(awayRatings.rating_elo ?? 1500);

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 space-y-8">
      {/* Top Breadcrumb */}
      <div className="flex flex-wrap items-center justify-between gap-4">
        <Link
          href="/"
          className="inline-flex items-center gap-2 text-xs font-mono font-semibold text-signal-emerald hover:underline"
        >
          <span>← Powrót do Pulpitu Analitycznego</span>
        </Link>
        <span className="text-xs font-mono text-text-muted tabular-nums">
          ID Zdarzenia: {breakdown.event_id} • Model: {breakdown.model_version}
        </span>
      </div>

      {/* Match Header Card */}
      <section className="rounded-xl border border-border-hairline bg-surface-slate p-6 space-y-4">
        <div className="flex flex-wrap items-center justify-between gap-3">
          <div className="flex items-center gap-2 text-xs font-mono">
            <span className="px-2.5 py-0.5 rounded bg-canvas-midnight text-signal-emerald border border-signal-emerald/30 uppercase font-bold">
              {breakdown.sport}
            </span>
            <span className="text-text-secondary font-sans font-semibold">
              {breakdown.league_name}
            </span>
          </div>
          <span className="text-xs font-mono text-text-muted tabular-nums">
            Start UTC: {breakdown.start_time_utc.replace("T", " ").replace("Z", " UTC")}
          </span>
        </div>

        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 pt-2">
          <div>
            <h1 className="text-2xl sm:text-3xl font-extrabold text-text-primary tracking-tight">
              {breakdown.home_team}{" "}
              <span className="text-text-muted font-normal">vs</span>{" "}
              {breakdown.away_team}
            </h1>
            <p className="text-xs text-text-secondary mt-1 font-mono">
              Aktywny silnik matematyczny:{" "}
              <span className="text-signal-emerald font-semibold">
                {breakdown.model_name}
              </span>
            </p>
          </div>

          <div className="flex items-center gap-3 font-mono tabular-nums">
            <div className="rounded-lg bg-canvas-midnight border border-border-hairline px-4 py-2.5 text-right">
              <div className="text-[10px] text-text-muted">ELO GOSPODARZ</div>
              <div className="text-base font-bold text-text-primary">
                {homeElo.toFixed(0)}
              </div>
            </div>
            <div className="rounded-lg bg-canvas-midnight border border-border-hairline px-4 py-2.5 text-right">
              <div className="text-[10px] text-text-muted">ELO GOŚĆ</div>
              <div className="text-base font-bold text-text-primary">
                {awayElo.toFixed(0)}
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* Middle 3-Card Row: Bayesian Fusion, Elo & Competitor Metrics, Factual Factors */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* 1. Bayesian Fusion Weights */}
        <section className="rounded-xl border border-border-hairline bg-surface-slate p-5 space-y-4">
          <div className="border-b border-border-hairline pb-3">
            <h2 className="text-sm font-bold text-text-primary">
              Wagi Fuzji Bayesowskiej (Model vs Rynek)
            </h2>
            <p className="text-xs text-text-muted">
              Synteza naszego modelu i odmarżowanego rynku ({breakdown.bayesian_fusion.sharp_bookmaker})
            </p>
          </div>

          <div className="space-y-3 font-mono text-xs tabular-nums">
            <div className="flex justify-between">
              <span className="text-text-secondary">
                Waga modelu własnego (p_model):
              </span>
              <span className="font-bold text-quant-teal">
                {formatPct(breakdown.bayesian_fusion.model_weight, 0)}
              </span>
            </div>
            <div className="flex justify-between">
              <span className="text-text-secondary">
                Waga rynku Sharp De-Vig (p_sharp):
              </span>
              <span className="font-bold text-signal-emerald">
                {formatPct(breakdown.bayesian_fusion.sharp_weight, 0)}
              </span>
            </div>

            {/* Visual proportion bar */}
            <div className="h-3 w-full rounded-full bg-canvas-midnight overflow-hidden flex border border-border-hairline">
              <div
                style={{
                  width: `${breakdown.bayesian_fusion.model_weight * 100}%`,
                }}
                className="bg-quant-teal h-full"
                title="Waga p_model"
              />
              <div
                style={{
                  width: `${breakdown.bayesian_fusion.sharp_weight * 100}%`,
                }}
                className="bg-signal-emerald h-full"
                title="Waga p_sharp"
              />
            </div>

            <div className="pt-2 text-[11px] font-sans text-text-muted leading-relaxed">
              Prawdopodobieństwo końcowe{" "}
              <span className="font-mono text-text-primary">p_true</span> stanowi
              ważoną kombinację log-odds modelu dziedzinowego oraz linii zamykającej
              Pinnacle oczyszczonej z marży algorytmem Shina.
            </div>
          </div>
        </section>

        {/* 2. Competitor Ratings & Sport Parameters */}
        <section className="rounded-xl border border-border-hairline bg-surface-slate p-5 space-y-4">
          <div className="border-b border-border-hairline pb-3">
            <h2 className="text-sm font-bold text-text-primary">
              Parametry Siły Drużyn / Zawodników
            </h2>
            <p className="text-xs text-text-muted">
              Wejściowe wskaźniki ratingowe i parametry rozkładu
            </p>
          </div>

          <div className="overflow-x-auto">
            <table className="w-full text-xs font-mono tabular-nums">
              <thead>
                <tr className="border-b border-border-hairline text-text-muted">
                  <th className="py-1.5 text-left font-sans">Parametr</th>
                  <th className="py-1.5 text-right">{breakdown.home_team}</th>
                  <th className="py-1.5 text-right">{breakdown.away_team}</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-border-hairline/60 text-text-secondary">
                <tr>
                  <td className="py-2 font-sans">Rating Elo</td>
                  <td className="py-2 text-right font-bold text-text-primary">
                    {homeElo.toFixed(0)}
                  </td>
                  <td className="py-2 text-right font-bold text-text-primary">
                    {awayElo.toFixed(0)}
                  </td>
                </tr>
                {homeRatings.xg_attack !== undefined && (
                  <tr>
                    <td className="py-2 font-sans">Atak xG / 90m</td>
                    <td className="py-2 text-right text-signal-emerald">
                      {Number(homeRatings.xg_attack).toFixed(2)}
                    </td>
                    <td className="py-2 text-right text-signal-emerald">
                      {Number(awayRatings.xg_attack ?? 1.2).toFixed(2)}
                    </td>
                  </tr>
                )}
                {homeRatings.pace !== undefined && (
                  <tr>
                    <td className="py-2 font-sans">Tempo (Pace) / ORtg</td>
                    <td className="py-2 text-right">
                      {Number(homeRatings.pace).toFixed(1)} /{" "}
                      {Number(homeRatings.ortg ?? 114).toFixed(1)}
                    </td>
                    <td className="py-2 text-right">
                      {Number(awayRatings.pace ?? 98).toFixed(1)} /{" "}
                      {Number(awayRatings.ortg ?? 112).toFixed(1)}
                    </td>
                  </tr>
                )}
                {homeRatings.serve_win_pct !== undefined && (
                  <tr>
                    <td className="py-2 font-sans">Wygrany serwis %</td>
                    <td className="py-2 text-right">
                      {formatPct(Number(homeRatings.serve_win_pct))}
                    </td>
                    <td className="py-2 text-right">
                      {formatPct(Number(awayRatings.serve_win_pct ?? 0.64))}
                    </td>
                  </tr>
                )}
              </tbody>
            </table>
          </div>

          {Object.keys(breakdown.sport_breakdown || {}).length > 0 && (
            <div className="pt-2 border-t border-border-hairline grid grid-cols-2 gap-2 text-[11px] font-mono tabular-nums">
              {Object.entries(breakdown.sport_breakdown)
                .slice(0, 4)
                .map(([key, value]) => (
                  <div
                    key={key}
                    className="rounded bg-canvas-midnight px-2.5 py-1.5 border border-border-hairline"
                  >
                    <div className="text-text-muted truncate">{key}</div>
                    <div className="font-bold text-text-primary">
                      {typeof value === "number"
                        ? value.toFixed(3)
                        : String(value)}
                    </div>
                  </div>
                ))}
            </div>
          )}
        </section>

        {/* 3. Factual Factors */}
        <section className="rounded-xl border border-border-hairline bg-surface-slate p-5 space-y-4">
          <div className="border-b border-border-hairline pb-3">
            <h2 className="text-sm font-bold text-text-primary">
              Czynniki Faktyczne (Factual Factors)
            </h2>
            <p className="text-xs text-text-muted">
              Determinanty matematyczne wpływające na wycenę
            </p>
          </div>

          <div className="space-y-2.5">
            {breakdown.factual_factors.map((factor, idx) => {
              const badgeColor =
                factor.impact === "positive"
                  ? "text-signal-emerald border-signal-emerald/30 bg-signal-emerald/10"
                  : factor.impact === "negative"
                  ? "text-semantic-loss border-semantic-loss/30 bg-semantic-loss/10"
                  : "text-text-secondary border-border-hairline bg-canvas-midnight";
              const symbol =
                factor.impact === "positive"
                  ? "▲ +"
                  : factor.impact === "negative"
                  ? "▼ -"
                  : "•";

              return (
                <div
                  key={`${factor.label}-${idx}`}
                  className="rounded-lg border border-border-hairline bg-canvas-midnight p-3 flex items-center justify-between gap-3"
                >
                  <span className="text-xs text-text-secondary font-medium">
                    {factor.label}
                  </span>
                  <span
                    className={`text-xs font-mono font-bold tabular-nums px-2 py-0.5 rounded border ${badgeColor}`}
                  >
                    {symbol} {factor.value}
                  </span>
                </div>
              );
            })}
          </div>
        </section>
      </div>

      {/* Clean SVG Probability Bar Chart */}
      {primaryMarket && (
        <section className="rounded-xl border border-border-hairline bg-surface-slate p-6 space-y-4">
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 border-b border-border-hairline pb-4">
            <div>
              <h2 className="text-base font-bold text-text-primary">
                Wykres Porównawczy Prawdopodobieństw: {primaryMarket.market_label}
              </h2>
              <p className="text-xs text-text-muted">
                Zestawienie słupkowe SVG: Model własny (<span className="font-mono text-quant-teal">p_model</span>),
                Rynek Sharp De-Vig (<span className="font-mono text-text-secondary">p_sharp</span>) oraz
                Fuzja Bayesowska (<span className="font-mono text-signal-emerald">p_true</span>).
              </p>
            </div>
            <div className="flex items-center gap-4 text-xs font-mono">
              <span className="flex items-center gap-1.5">
                <span className="w-3 h-3 rounded-sm bg-quant-teal inline-block" />
                p_model
              </span>
              <span className="flex items-center gap-1.5">
                <span className="w-3 h-3 rounded-sm bg-text-secondary inline-block" />
                p_sharp
              </span>
              <span className="flex items-center gap-1.5">
                <span className="w-3 h-3 rounded-sm bg-signal-emerald inline-block" />
                p_true (Fuzja)
              </span>
            </div>
          </div>

          <div className="w-full overflow-x-auto">
            <svg
              viewBox="0 0 760 240"
              className="w-full h-auto max-h-64 bg-canvas-midnight rounded-lg border border-border-hairline p-3"
              role="img"
              aria-label="Wykres słupkowy prawdopodobieństw p_model, p_sharp i p_true"
            >
              {/* Horizontal Grid Lines */}
              {[0, 0.25, 0.5, 0.75, 1.0].map((tick) => {
                const y = 190 - tick * 150;
                return (
                  <g key={tick}>
                    <line
                      x1="60"
                      y1={y}
                      x2="720"
                      y2={y}
                      stroke="#23324D"
                      strokeDasharray={tick === 0 ? undefined : "4 4"}
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
                      {Math.round(tick * 100)}%
                    </text>
                  </g>
                );
              })}

              {/* Bars per Outcome */}
              {primaryMarket.outcomes.map((out, idx) => {
                const groupWidth = 640 / Math.max(primaryMarket.outcomes.length, 1);
                const baseX = 80 + idx * groupWidth;
                const hModel = Math.max(2, out.p_model * 150);
                const hSharp = Math.max(2, out.p_sharp * 150);
                const hTrue = Math.max(2, out.p_true * 150);

                return (
                  <g key={out.outcome_key}>
                    {/* p_model bar */}
                    <rect
                      x={baseX}
                      y={190 - hModel}
                      width="34"
                      height={hModel}
                      rx="3"
                      fill="#0D9488"
                    />
                    <text
                      x={baseX + 17}
                      y={184 - hModel}
                      textAnchor="middle"
                      fill="#CBD5E1"
                      fontSize="10"
                      fontFamily="monospace"
                    >
                      {(out.p_model * 100).toFixed(1)}%
                    </text>

                    {/* p_sharp bar */}
                    <rect
                      x={baseX + 42}
                      y={190 - hSharp}
                      width="34"
                      height={hSharp}
                      rx="3"
                      fill="#CBD5E1"
                    />
                    <text
                      x={baseX + 59}
                      y={184 - hSharp}
                      textAnchor="middle"
                      fill="#CBD5E1"
                      fontSize="10"
                      fontFamily="monospace"
                    >
                      {(out.p_sharp * 100).toFixed(1)}%
                    </text>

                    {/* p_true bar */}
                    <rect
                      x={baseX + 84}
                      y={190 - hTrue}
                      width="34"
                      height={hTrue}
                      rx="3"
                      fill="#10B981"
                    />
                    <text
                      x={baseX + 101}
                      y={184 - hTrue}
                      textAnchor="middle"
                      fill="#10B981"
                      fontSize="10"
                      fontWeight="bold"
                      fontFamily="monospace"
                    >
                      {(out.p_true * 100).toFixed(1)}%
                    </text>

                    {/* Outcome Label */}
                    <text
                      x={baseX + 59}
                      y="214"
                      textAnchor="middle"
                      fill="#F8FAFC"
                      fontSize="12"
                      fontWeight="bold"
                    >
                      {out.outcome_label}
                    </text>
                  </g>
                );
              })}
            </svg>
          </div>
        </section>
      )}

      {/* Full Markets Table */}
      <section className="rounded-xl border border-border-hairline bg-surface-slate p-6 space-y-5">
        <div>
          <h2 className="text-base font-bold text-text-primary">
            Pełna Tabela Rynków, Kursów Sprawiedliwych (Fair Odds) i EV Netto
          </h2>
          <p className="text-xs text-text-muted">
            Porównanie EV w trybie Bez Podatku (1.00×) oraz z ustawowym 12% podatkiem obrotowym (0.88×).
          </p>
        </div>

        <div className="space-y-6">
          {breakdown.available_markets.map((mkt) => (
            <div
              key={mkt.market_key}
              className="rounded-lg border border-border-hairline bg-canvas-midnight overflow-hidden"
            >
              <div className="px-4 py-2.5 bg-surface-elevated/60 border-b border-border-hairline flex items-center justify-between">
                <span className="text-xs font-bold text-text-primary">
                  {mkt.market_label}
                </span>
                <span className="text-[11px] font-mono text-text-muted">
                  Kod rynku: {mkt.market_key}
                </span>
              </div>
              <div className="overflow-x-auto">
                <table className="w-full text-left border-collapse text-xs font-mono tabular-nums">
                  <thead>
                    <tr className="border-b border-border-hairline text-text-muted">
                      <th className="py-2.5 px-3 font-sans">Selekcja</th>
                      <th className="py-2.5 px-3">Bukmacher PL</th>
                      <th className="py-2.5 px-3 text-right">p_model</th>
                      <th className="py-2.5 px-3 text-right">p_sharp</th>
                      <th className="py-2.5 px-3 text-right text-signal-emerald">
                        p_true
                      </th>
                      <th className="py-2.5 px-3 text-right">Fair Odds</th>
                      <th className="py-2.5 px-3 text-right text-alpha-amber">
                        Kurs PL
                      </th>
                      <th className="py-2.5 px-3 text-right">EV (1.00×)</th>
                      <th className="py-2.5 px-3 text-right">EV (0.88×)</th>
                      <th className="py-2.5 px-3 text-right">Kelly 0.25×</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-border-hairline">
                    {mkt.outcomes.map((out) => {
                      const evTf = formatEv(out.ev_taxfree_pl);
                      const evStd = formatEv(out.ev_standard_pl);
                      return (
                        <tr
                          key={out.outcome_key}
                          className="hover:bg-surface-elevated/30"
                        >
                          <td className="py-2.5 px-3 font-sans font-semibold text-text-primary">
                            {out.outcome_label}
                          </td>
                          <td className="py-2.5 px-3 uppercase text-text-secondary">
                            {out.best_bookmaker}
                          </td>
                          <td className="py-2.5 px-3 text-right text-text-secondary">
                            {formatPct(out.p_model)}
                          </td>
                          <td className="py-2.5 px-3 text-right text-text-secondary">
                            {formatPct(out.p_sharp)}
                          </td>
                          <td className="py-2.5 px-3 text-right font-bold text-text-primary">
                            {formatPct(out.p_true)}
                          </td>
                          <td className="py-2.5 px-3 text-right text-text-secondary">
                            {out.fair_odds.toFixed(2)}
                          </td>
                          <td className="py-2.5 px-3 text-right font-bold text-alpha-amber">
                            {out.odds_decimal.toFixed(2)}
                          </td>
                          <td
                            className={`py-2.5 px-3 text-right font-bold ${
                              evTf.isPositive
                                ? "text-signal-emerald"
                                : "text-semantic-loss"
                            }`}
                          >
                            {evTf.text}
                          </td>
                          <td
                            className={`py-2.5 px-3 text-right ${
                              evStd.isPositive
                                ? "text-signal-emerald"
                                : "text-semantic-loss"
                            }`}
                          >
                            {evStd.text}
                          </td>
                          <td className="py-2.5 px-3 text-right text-text-secondary">
                            {formatPct(out.kelly_fraction, 2)}
                          </td>
                        </tr>
                      );
                    })}
                  </tbody>
                </table>
              </div>
            </div>
          ))}
        </div>
      </section>
    </div>
  );
}

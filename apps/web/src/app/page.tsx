"use client";

import React, { useCallback, useEffect, useMemo, useState } from "react";
import Link from "next/link";
import {
  ACTIVE_V1_SPORTS,
  ActiveSportSlug,
  BookmakerMode,
  CandidateSelection,
  EvaluatedSlip,
  evaluateSlip,
  fetchCategories,
  fetchEvents,
  GeneratedSlipProposal,
  generateSlips,
  LegInput,
  MarketOutcomeDetail,
  PreMatchEventItem,
  RiskProfile,
  saveSlip,
  SportCategoryItem,
} from "../lib/api";

const BOOKMAKER_MODES: ReadonlyArray<{
  value: BookmakerMode;
  label: string;
  badge: string;
  desc: string;
}> = [
  {
    value: "betclic_tax_free",
    label: "Betclic Bez Podatku (1.00×)",
    badge: "1.00× (≥2 nogi, kurs ≥1.20)",
    desc: "Brak 12% podatku obrotowego dla kuponów AKO ≥2 zdarzenia (min. kurs 1.20).",
  },
  {
    value: "fortuna_promo",
    label: "Fortuna AKO Bez Podatku (1.00×)",
    badge: "1.00× (≥3 nogi, kurs ≥1.30)",
    desc: "Mnożnik 1.00× przy min. 3 zdarzeniach z kursem pojedynczym ≥1.30.",
  },
  {
    value: "superbet_boost",
    label: "Superbet Promo (1.00×)",
    badge: "1.00× (≥3 nogi, kurs ≥1.25)",
    desc: "Promocyjny mnożnik 1.00× od 3 zdarzeń z kursem min. 1.25.",
  },
  {
    value: "standard_088",
    label: "Standard PL 12% Podatek (0.88×)",
    badge: "0.88× Ustawowy",
    desc: "Standardowy polski podatek od gier 12% (współczynnik 0.88× od stawki).",
  },
];

const RISK_PROFILES: ReadonlyArray<{
  value: RiskProfile;
  label: string;
  desc: string;
}> = [
  {
    value: "conservative",
    label: "Konserwatywny (Max P)",
    desc: "Priorytet maksymalizacji łącznego prawdopodobieństwa wejścia P(kupon).",
  },
  {
    value: "balanced",
    label: "Zbalansowany (Quant Core)",
    desc: "Optymalny balans pomiędzy szansą trafienia a dodatnim EV netto.",
  },
  {
    value: "aggressive",
    label: "Agresywny (+EV Edge)",
    desc: "Wyższa waga dla przewagi kursowej nad linią de-vigged Pinnacle.",
  },
  {
    value: "max_value",
    label: "Maksymalne Value (Pure EV)",
    desc: "Ścisła maksymalizacja wartości oczekiwanej EV netto.",
  },
];

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

export default function DashboardPage() {
  const [selectedSport, setSelectedSport] = useState<ActiveSportSlug | "all">("all");
  const [categories, setCategories] = useState<SportCategoryItem[]>([]);
  const [events, setEvents] = useState<PreMatchEventItem[]>([]);
  const [loadingEvents, setLoadingEvents] = useState<boolean>(true);
  const [onlyPlusEvFilter, setOnlyPlusEvFilter] = useState<boolean>(false);

  // Combinatorial Slip Generator state
  const [generatorSports, setGeneratorSports] = useState<ActiveSportSlug[]>([
    "football",
    "basketball",
    "tennis",
    "hockey",
  ]);
  const [riskProfile, setRiskProfile] = useState<RiskProfile>("balanced");
  const [targetOddsMin, setTargetOddsMin] = useState<number>(2.2);
  const [targetOddsMax, setTargetOddsMax] = useState<number>(5.5);
  const [minLegs, setMinLegs] = useState<number>(2);
  const [maxLegs, setMaxLegs] = useState<number>(4);
  const [stake, setStake] = useState<number>(100);
  const [bookmakerMode, setBookmakerMode] = useState<BookmakerMode>("betclic_tax_free");
  const [onlyPlusEvGenerator, setOnlyPlusEvGenerator] = useState<boolean>(false);

  // Active Evaluated Slip & Proposals
  const [proposals, setProposals] = useState<GeneratedSlipProposal[]>([]);
  const [activeSlip, setActiveSlip] = useState<EvaluatedSlip | null>(null);
  const [oddsOverrides, setOddsOverrides] = useState<Record<string, number>>({});
  const [solverMeta, setSolverMeta] = useState<{
    poolSize: number;
    elapsedMs: number;
    algorithm: string;
  } | null>(null);
  const [generating, setGenerating] = useState<boolean>(false);
  const [evaluating, setEvaluating] = useState<boolean>(false);

  // Save Slip state
  const [slipName, setSlipName] = useState<string>("Kupon LeadBet");
  const [savingSlip, setSavingSlip] = useState<boolean>(false);
  const [savedNotice, setSavedNotice] = useState<string | null>(null);
  const [errorBanner, setErrorBanner] = useState<string | null>(null);

  // Load categories & initial events + initial generated slip
  useEffect(() => {
    let mounted = true;
    async function initLoad() {
      setLoadingEvents(true);
      try {
        const [catRes, evRes, genRes] = await Promise.all([
          fetchCategories(true),
          fetchEvents({ limit: 50 }),
          generateSlips({
            sports: ["football", "basketball", "tennis", "hockey"],
            risk_profile: "balanced",
            target_odds_min: 2.2,
            target_odds_max: 5.5,
            min_legs: 2,
            max_legs: 4,
            stake: 100,
            bookmaker_mode: "betclic_tax_free",
            only_plus_ev: false,
          }),
        ]);
        if (!mounted) return;
        const activeSlugs = new Set<string>(ACTIVE_V1_SPORTS.map((s) => s.slug));
        setCategories(
          catRes.categories.filter((c) => activeSlugs.has(c.slug) && c.is_enabled_v1)
        );
        setEvents(
          evRes.events.filter((ev) => activeSlugs.has(ev.sport_slug))
        );
        if (genRes.coupons.length > 0) {
          setProposals(genRes.coupons);
          setActiveSlip(genRes.coupons[0]);
          setSolverMeta({
            poolSize: genRes.candidate_pool_size,
            elapsedMs: genRes.execution_time_ms,
            algorithm: genRes.solver_algorithm,
          });
        }
      } catch (err) {
        if (mounted) {
          setErrorBanner(
            err instanceof Error ? err.message : "Błąd komunikacji z silnikiem API"
          );
        }
      } finally {
        if (mounted) setLoadingEvents(false);
      }
    }
    initLoad();
    return () => {
      mounted = false;
    };
  }, []);

  const filteredEvents = useMemo(() => {
    const activeSlugs = new Set<string>(ACTIVE_V1_SPORTS.map((s) => s.slug));
    return events.filter((ev) => {
      if (!activeSlugs.has(ev.sport_slug)) return false;
      if (selectedSport !== "all" && ev.sport_slug !== selectedSport) return false;
      if (onlyPlusEvFilter && ev.max_ev_net <= 0) return false;
      return true;
    });
  }, [events, selectedSport, onlyPlusEvFilter]);

  const runEvaluateSelections = useCallback(
    async (
      selections: CandidateSelection[],
      nextOverrides: Record<string, number>,
      nextStake: number,
      nextMode: BookmakerMode
    ) => {
      if (selections.length === 0) {
        setActiveSlip(null);
        return;
      }
      setEvaluating(true);
      setErrorBanner(null);
      try {
        const legInputs: LegInput[] = selections.map((sel) => {
          const legKey = `${sel.event_id}:${sel.market_key}:${sel.outcome_key}`;
          const override = nextOverrides[legKey];
          return {
            event_id: sel.event_id,
            market_key: sel.market_key,
            outcome_key: sel.outcome_key,
            bookmaker_key: sel.bookmaker_key,
            odds_override: override !== undefined ? override : sel.odds_gross,
          };
        });
        const evaluated = await evaluateSlip({
          selections: legInputs,
          stake: Math.max(1, nextStake),
          bookmaker_mode: nextMode,
        });
        setActiveSlip(evaluated);
      } catch (err) {
        setErrorBanner(
          err instanceof Error ? err.message : "Nie udało się przeliczyć kuponu."
        );
      } finally {
        setEvaluating(false);
      }
    },
    []
  );

  const handleGenerateSlips = async (e?: React.FormEvent) => {
    if (e) e.preventDefault();
    setGenerating(true);
    setErrorBanner(null);
    setSavedNotice(null);
    try {
      const sportsToUse =
        generatorSports.length > 0
          ? generatorSports
          : (["football", "basketball", "tennis", "hockey"] as ActiveSportSlug[]);
      const res = await generateSlips({
        sports: sportsToUse,
        risk_profile: riskProfile,
        target_odds_min: Math.max(1.1, targetOddsMin),
        target_odds_max: Math.max(targetOddsMin + 0.2, targetOddsMax),
        min_legs: Math.max(1, minLegs),
        max_legs: Math.max(minLegs, maxLegs),
        stake: Math.max(1, stake),
        bookmaker_mode: bookmakerMode,
        only_plus_ev: onlyPlusEvGenerator,
        custom_overrides: oddsOverrides,
      });
      setProposals(res.coupons);
      setSolverMeta({
        poolSize: res.candidate_pool_size,
        elapsedMs: res.execution_time_ms,
        algorithm: res.solver_algorithm,
      });
      if (res.coupons.length > 0) {
        setActiveSlip(res.coupons[0]);
      }
    } catch (err) {
      setErrorBanner(
        err instanceof Error ? err.message : "Błąd generowania kuponu optymalnego."
      );
    } finally {
      setGenerating(false);
    }
  };

  // 1-click Polish odds override per leg calling POST /api/v1/slips/evaluate
  const handleLegOddsOverride = async (
    sel: CandidateSelection,
    newOddsValue: number
  ) => {
    if (!activeSlip) return;
    const clampedOdds = Number(Math.max(1.01, newOddsValue).toFixed(2));
    const legKey = `${sel.event_id}:${sel.market_key}:${sel.outcome_key}`;
    const nextOverrides = {
      ...oddsOverrides,
      [legKey]: clampedOdds,
    };
    setOddsOverrides(nextOverrides);
    await runEvaluateSelections(
      activeSlip.selections,
      nextOverrides,
      stake,
      bookmakerMode
    );
  };

  const handleStakeOrModeChange = async (
    nextStake: number,
    nextMode: BookmakerMode
  ) => {
    setStake(nextStake);
    setBookmakerMode(nextMode);
    if (activeSlip && activeSlip.selections.length > 0) {
      await runEvaluateSelections(
        activeSlip.selections,
        oddsOverrides,
        nextStake,
        nextMode
      );
    }
  };

  const handleToggleOutcomeOnSlip = async (
    ev: PreMatchEventItem,
    outcome: MarketOutcomeDetail
  ) => {
    const currentSelections = activeSlip?.selections || [];
    const existingIdx = currentSelections.findIndex(
      (s) =>
        s.event_id === ev.id &&
        s.market_key === ev.primary_market.market_key &&
        s.outcome_key === outcome.outcome_key
    );

    let nextSelections: CandidateSelection[];
    if (existingIdx >= 0) {
      nextSelections = currentSelections.filter((_, idx) => idx !== existingIdx);
    } else {
      // Replace any other selection from the same event (Anti-Correlation Guard)
      const withoutSameEvent = currentSelections.filter((s) => s.event_id !== ev.id);
      const newCandidate: CandidateSelection = {
        event_id: ev.id,
        event_name: `${ev.home_team} vs ${ev.away_team}`,
        sport: ev.sport_slug,
        league_name: ev.league_name,
        start_time_utc: ev.start_time_utc,
        market_key: ev.primary_market.market_key,
        market_label: ev.primary_market.market_label,
        outcome_key: outcome.outcome_key,
        outcome_label: outcome.outcome_label,
        bookmaker_key: outcome.best_bookmaker,
        odds_gross: outcome.odds_decimal,
        p_model: outcome.p_model,
        p_sharp: outcome.p_sharp,
        p_true: outcome.p_true,
        ev_net: outcome.ev_taxfree_pl,
        applied_tax_multiplier: 1.0,
      };
      nextSelections = [...withoutSameEvent, newCandidate];
    }

    await runEvaluateSelections(nextSelections, oddsOverrides, stake, bookmakerMode);
  };

  const handleRemoveLeg = async (eventId: string, marketKey: string, outcomeKey: string) => {
    if (!activeSlip) return;
    const nextSelections = activeSlip.selections.filter(
      (s) =>
        !(
          s.event_id === eventId &&
          s.market_key === marketKey &&
          s.outcome_key === outcomeKey
        )
    );
    await runEvaluateSelections(nextSelections, oddsOverrides, stake, bookmakerMode);
  };

  const handleSaveActiveSlip = async () => {
    if (!activeSlip || activeSlip.selections.length === 0) return;
    setSavingSlip(true);
    setSavedNotice(null);
    setErrorBanner(null);
    try {
      const legInputs: LegInput[] = activeSlip.selections.map((s) => ({
        event_id: s.event_id,
        market_key: s.market_key,
        outcome_key: s.outcome_key,
        bookmaker_key: s.bookmaker_key,
        odds_override: s.odds_gross,
      }));
      const res = await saveSlip({
        name: slipName.trim() || "Kupon LeadBet",
        selections: legInputs,
        stake: activeSlip.stake,
        bookmaker_mode: bookmakerMode,
        bookmaker_key: activeSlip.selections[0]?.bookmaker_key || "betclic",
      });
      setSavedNotice(`Zapisano kupon "${res.slip.name}" (ID: ${res.slip.id.slice(0, 8)})`);
    } catch (err) {
      setErrorBanner(
        err instanceof Error ? err.message : "Nie udało się zapisać kuponu."
      );
    } finally {
      setSavingSlip(false);
    }
  };

  const toggleGeneratorSport = (slug: ActiveSportSlug) => {
    setGeneratorSports((prev) =>
      prev.includes(slug) ? prev.filter((s) => s !== slug) : [...prev, slug]
    );
  };

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 pt-6 pb-24 lg:pb-8 space-y-6">
      <div className="flex flex-col sm:flex-row sm:items-baseline sm:justify-between gap-2 border-b border-border-hairline pb-4">
        <h1 className="text-xl font-bold tracking-tight text-text-primary">
          Analiza pre-match i generator kuponów
        </h1>
        <p className="text-xs font-mono text-text-muted tabular-nums">
          4 aktywne dyscypliny • Podatek PL (0.88× / 1.00×) • Próg PIT &gt; 2280 PLN
        </p>
      </div>

      {errorBanner && (
        <div className="rounded-lg border border-semantic-loss/40 bg-semantic-loss/10 px-4 py-3 text-xs text-semantic-loss font-mono flex items-center justify-between">
          <span>▼ Błąd: {errorBanner}</span>
          <button
            type="button"
            onClick={() => setErrorBanner(null)}
            className="underline ml-4"
          >
            Zamknij
          </button>
        </div>
      )}

      {/* 4 Active Sport Tabs (Strictly Football, Basketball, Tennis, Hockey) */}
      <section aria-label="Wybór dyscypliny sportowej" className="space-y-3">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
          <div className="flex items-center gap-2 overflow-x-auto pb-1 -mx-4 px-4 sm:mx-0 sm:px-0 sm:pb-0 sm:flex-wrap">
            <button
              type="button"
              onClick={() => setSelectedSport("all")}
              className={`shrink-0 px-3.5 py-2 rounded-lg text-xs font-mono font-semibold border transition-colors ${
                selectedSport === "all"
                  ? "bg-signal-emerald text-canvas-obsidian border-signal-emerald"
                  : "bg-surface-slate text-text-secondary border-border-hairline hover:bg-surface-elevated"
              }`}
            >
              Wszystkie (4)
            </button>
            {ACTIVE_V1_SPORTS.map((sp) => {
              const catInfo = categories.find((c) => c.slug === sp.slug);
              const isSelected = selectedSport === sp.slug;
              return (
                <button
                  key={sp.slug}
                  type="button"
                  onClick={() => setSelectedSport(sp.slug)}
                  className={`shrink-0 px-3.5 py-2 rounded-lg text-xs font-medium border transition-colors flex items-center gap-2 ${
                    isSelected
                      ? "bg-surface-elevated text-signal-emerald border-signal-emerald font-semibold"
                      : "bg-surface-slate text-text-secondary border-border-hairline hover:bg-surface-elevated hover:text-text-primary"
                  }`}
                >
                  <span>{sp.name_pl}</span>
                  <span className="font-mono text-[10px] px-1.5 py-0.5 rounded bg-canvas-midnight text-text-muted tabular-nums">
                    {catInfo?.fixtures_count ??
                      events.filter((e) => e.sport_slug === sp.slug).length}
                  </span>
                </button>
              );
            })}
          </div>

          <label className="inline-flex items-center gap-2 text-xs text-text-secondary cursor-pointer select-none bg-surface-slate px-3 py-2 rounded-lg border border-border-hairline">
            <input
              type="checkbox"
              checked={onlyPlusEvFilter}
              onChange={(e) => setOnlyPlusEvFilter(e.target.checked)}
              className="rounded border-border-hairline bg-canvas-obsidian text-signal-emerald focus:ring-signal-emerald"
            />
            <span>Tylko zdarzenia z dodatnim +EV</span>
          </label>
        </div>
      </section>

      {/* Main 12-Column Analytical Grid: Left (7 cols) Events Table, Right (5 cols) Combinatorial Slip Generator & Evaluator */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-8 items-start">
        {/* LEFT COLUMN: Pre-Match Events List */}
        <section className="lg:col-span-7 space-y-4">
          <div className="flex items-center justify-between">
            <div>
              <h2 className="text-lg font-bold text-text-primary">
                Zdarzenia Pre-Match i Dekompozycja Prawdopodobieństw
              </h2>
              <p className="text-xs text-text-muted">
                Kliknij dowolny kurs, aby dodać lub usunąć zdarzenie z kuponu, lub przejdź do pełnego rozkładu meczu.
              </p>
            </div>
            <span className="text-xs text-text-muted tabular-nums">
              Mecze: <span className="font-mono font-medium text-text-primary">{filteredEvents.length}</span>
            </span>
          </div>

          {loadingEvents ? (
            <div className="space-y-4" aria-label="Ładowanie zdarzeń">
              {[0, 1, 2].map((idx) => (
                <div
                  key={idx}
                  className="rounded-xl border border-border-hairline bg-surface-slate p-4 space-y-3 animate-pulse"
                >
                  <div className="h-4 w-48 rounded bg-surface-elevated" />
                  <div className="h-10 w-full rounded bg-canvas-midnight" />
                  <div className="h-10 w-full rounded bg-canvas-midnight" />
                </div>
              ))}
            </div>
          ) : filteredEvents.length === 0 ? (
            <div className="rounded-xl border border-border-hairline bg-surface-slate p-8 text-center space-y-2">
              <div className="text-sm font-semibold text-alpha-amber">
                ▲ Brak zdarzeń spełniających wybrane kryteria filtrów
              </div>
              <p className="text-xs text-text-muted">
                Zmień aktywną dyscyplinę lub wyłącz filtr dodatniego +EV.
              </p>
            </div>
          ) : (
            <div className="rounded-lg border border-border-hairline bg-surface-slate divide-y divide-border-hairline">
              {filteredEvents.map((ev) => {
                return (
                  <article key={ev.id} className="p-4 space-y-3">
                    <div className="flex flex-wrap items-center justify-between gap-2 text-xs">
                      <div className="flex flex-wrap items-center gap-x-2 gap-y-0.5 text-text-muted">
                        <span className="font-medium text-text-secondary">
                          {ev.sport_name_pl}
                        </span>
                        <span>·</span>
                        <span>{ev.league_name}</span>
                        {ev.surface_or_format && (
                          <span className="text-text-muted/80">
                            ({ev.surface_or_format})
                          </span>
                        )}
                        <span>·</span>
                        <span className="font-mono tabular-nums">
                          {ev.start_time_utc.replace("T", " ").replace(":00Z", " UTC")}
                        </span>
                      </div>

                      <Link
                        href={`/events/${ev.id}`}
                        className="text-xs font-medium text-brand-sky hover:underline shrink-0"
                      >
                        Analiza →
                      </Link>
                    </div>

                    <div className="flex flex-wrap items-baseline justify-between gap-2">
                      <h3 className="text-sm sm:text-base font-semibold text-text-primary">
                        <Link
                          href={`/events/${ev.id}`}
                          className="hover:text-brand-sky transition-colors duration-150"
                        >
                          {ev.home_team} <span className="text-text-muted font-normal">vs</span>{" "}
                          {ev.away_team}
                        </Link>
                      </h3>
                      <span className="text-[11px] text-text-muted">
                        {ev.primary_market.market_label}
                      </span>
                    </div>

                      {/* Mobile Outcomes Card List (< sm) */}
                      <div className="sm:hidden space-y-2">
                        {ev.primary_market.outcomes.map((out) => {
                          const activeEv =
                            bookmakerMode === "standard_088"
                              ? out.ev_standard_pl
                              : out.ev_taxfree_pl;
                          const evBadge = formatEv(activeEv);
                          const isSelectedInSlip = Boolean(
                            activeSlip?.selections.some(
                              (s) =>
                                s.event_id === ev.id &&
                                s.market_key === ev.primary_market.market_key &&
                                s.outcome_key === out.outcome_key
                            )
                          );

                          return (
                            <div
                              key={out.outcome_key}
                              className={`rounded-lg border p-3 flex items-center justify-between gap-3 ${
                                isSelectedInSlip
                                  ? "border-signal-emerald/60 bg-signal-emerald/10"
                                  : "border-border-hairline bg-canvas-midnight"
                              }`}
                            >
                              <div className="min-w-0 space-y-1">
                                <div className="text-sm font-semibold text-text-primary truncate">
                                  {out.outcome_label}
                                </div>
                                <div className="flex flex-wrap items-center gap-x-2.5 gap-y-0.5 text-[11px] font-mono tabular-nums text-text-muted">
                                  <span className="uppercase">{out.best_bookmaker}</span>
                                  <span>p_true: {formatPct(out.p_true)}</span>
                                  <span
                                    className={
                                      evBadge.isPositive
                                        ? "text-signal-emerald font-semibold"
                                        : "text-semantic-loss font-semibold"
                                    }
                                  >
                                    EV {evBadge.text}
                                  </span>
                                </div>
                              </div>

                              <button
                                type="button"
                                onClick={() => handleToggleOutcomeOnSlip(ev, out)}
                                className={`shrink-0 min-h-[40px] px-3 py-2 rounded-lg font-mono text-xs font-bold tabular-nums transition-colors ${
                                  isSelectedInSlip
                                    ? "bg-signal-emerald text-canvas-obsidian"
                                    : "bg-surface-elevated text-alpha-amber border border-border-hairline"
                                }`}
                              >
                                {out.odds_decimal.toFixed(2)} •{" "}
                                {isSelectedInSlip ? "✓" : "+"}
                              </button>
                            </div>
                          );
                        })}
                      </div>

                      {/* Desktop Outcomes Mathematical Table (>= sm) */}
                      <div className="hidden sm:block overflow-x-auto">
                        <table className="w-full text-left border-collapse text-xs font-mono tabular-nums">
                          <thead>
                            <tr className="border-b border-border-hairline text-text-muted bg-surface-elevated/40">
                              <th className="py-2 px-3 font-sans font-medium">Typ</th>
                              <th className="py-2 px-2.5 text-right" title="Prawdopodobieństwo modelu sportowego">
                                p_model
                              </th>
                              <th className="py-2 px-2.5 text-right" title="Prawdopodobieństwo Pinnacle po de-viggingu Shina">
                                p_sharp
                              </th>
                              <th className="py-2 px-2.5 text-right text-signal-emerald" title="Prawdopodobieństwo po fuzji bayesowskiej">
                                p_true
                              </th>
                              <th className="py-2 px-2.5 text-right">Kurs PL</th>
                              <th className="py-2 px-2.5 text-right" title="Wartość oczekiwana netto (1.00× / 0.88×)">
                                Net EV
                              </th>
                              <th className="py-2 px-2.5 text-right">Akcja</th>
                            </tr>
                          </thead>
                          <tbody className="divide-y divide-border-hairline">
                            {ev.primary_market.outcomes.map((out) => {
                              const activeEv =
                                bookmakerMode === "standard_088"
                                  ? out.ev_standard_pl
                                  : out.ev_taxfree_pl;
                              const evBadge = formatEv(activeEv);
                              const isSelectedInSlip = Boolean(
                                activeSlip?.selections.some(
                                  (s) =>
                                    s.event_id === ev.id &&
                                    s.market_key === ev.primary_market.market_key &&
                                    s.outcome_key === out.outcome_key
                                )
                              );

                              return (
                                <tr
                                  key={out.outcome_key}
                                  className={`transition-colors ${
                                    isSelectedInSlip
                                      ? "bg-signal-emerald/10"
                                      : "hover:bg-surface-elevated/40"
                                  }`}
                                >
                                  <td className="py-2.5 px-3 font-sans font-medium text-text-primary">
                                    <div>{out.outcome_label}</div>
                                    <div className="text-[10px] font-mono text-text-muted uppercase">
                                      {out.best_bookmaker} • Fair: {out.fair_odds.toFixed(2)}
                                    </div>
                                  </td>
                                  <td className="py-2.5 px-2.5 text-right text-text-secondary">
                                    {formatPct(out.p_model)}
                                  </td>
                                  <td className="py-2.5 px-2.5 text-right text-text-secondary">
                                    {formatPct(out.p_sharp)}
                                  </td>
                                  <td className="py-2.5 px-2.5 text-right font-bold text-text-primary">
                                    {formatPct(out.p_true)}
                                  </td>
                                  <td className="py-2.5 px-2.5 text-right font-bold text-alpha-amber">
                                    {out.odds_decimal.toFixed(2)}
                                  </td>
                                  <td
                                    className={`py-2.5 px-2.5 text-right font-semibold ${
                                      evBadge.isPositive
                                        ? "text-signal-emerald"
                                        : "text-semantic-loss"
                                    }`}
                                  >
                                    {evBadge.text}
                                  </td>
                                  <td className="py-2.5 px-2.5 text-right">
                                    <button
                                      type="button"
                                      onClick={() => handleToggleOutcomeOnSlip(ev, out)}
                                      className={`px-2.5 py-1 rounded text-[11px] font-sans font-semibold transition-colors ${
                                        isSelectedInSlip
                                          ? "bg-signal-emerald text-canvas-obsidian"
                                          : "bg-surface-elevated text-text-primary border border-border-hairline hover:border-signal-emerald"
                                      }`}
                                    >
                                      {isSelectedInSlip ? "✓ W kuponie" : "+ Kupon"}
                                    </button>
                                  </td>
                                </tr>
                              );
                            })}
                          </tbody>
                        </table>
                      </div>
                  </article>
                );
              })}
            </div>
          )}
        </section>

        {/* RIGHT COLUMN: Combinatorial Slip Generator & Active Polish Tax Evaluator */}
        <aside id="kupon-panel" className="lg:col-span-5 space-y-6 scroll-mt-20">
          {/* Combinatorial Slip Generator Panel */}
          <div className="rounded-xl border border-border-hairline bg-surface-slate p-5 space-y-5">
            <div className="border-b border-border-hairline pb-3">
              <h2 className="text-base font-bold text-text-primary">
                Generator kuponu
              </h2>
              <p className="text-xs text-text-muted">
                Maksymalizacja P(kupon) w zadanym zakresie kursów (maks. 1 typ z meczu)
              </p>
            </div>

            <form onSubmit={handleGenerateSlips} className="space-y-4 text-xs">
              {/* Bookmaker Tax Mode Selector */}
              <div className="space-y-1.5">
                <label
                  htmlFor="bookmaker-mode-select"
                  className="block font-medium text-text-secondary"
                >
                  Tryb podatku / promocji bukmachera PL:
                </label>
                <select
                  id="bookmaker-mode-select"
                  value={bookmakerMode}
                  onChange={(e) =>
                    handleStakeOrModeChange(stake, e.target.value as BookmakerMode)
                  }
                  className="w-full rounded-lg bg-canvas-midnight border border-border-hairline px-3 py-2 text-base sm:text-xs text-text-primary font-mono focus:outline-none focus:border-signal-emerald"
                >
                  {BOOKMAKER_MODES.map((m) => (
                    <option key={m.value} value={m.value}>
                      {m.label}
                    </option>
                  ))}
                </select>
                <p className="text-[11px] text-text-muted">
                  {BOOKMAKER_MODES.find((m) => m.value === bookmakerMode)?.desc}
                </p>
              </div>

              {/* Risk Profile Selector */}
              <div className="space-y-1.5">
                <label
                  htmlFor="risk-profile-select"
                  className="block font-medium text-text-secondary"
                >
                  Profil ryzyka (funkcja celu):
                </label>
                <select
                  id="risk-profile-select"
                  value={riskProfile}
                  onChange={(e) => setRiskProfile(e.target.value as RiskProfile)}
                  className="w-full rounded-lg bg-canvas-midnight border border-border-hairline px-3 py-2 text-text-primary focus:outline-none focus:border-signal-emerald"
                >
                  {RISK_PROFILES.map((rp) => (
                    <option key={rp.value} value={rp.value}>
                      {rp.label}
                    </option>
                  ))}
                </select>
              </div>

              {/* Target Odds Min / Max & Min / Max Legs */}
              <div className="grid grid-cols-2 gap-3 font-mono tabular-nums">
                <div>
                  <label
                    htmlFor="target-odds-min"
                    className="block font-sans text-text-secondary mb-1"
                  >
                    Kurs docelowy min:
                  </label>
                  <input
                    id="target-odds-min"
                    type="number"
                    step="0.1"
                    min="1.1"
                    max="100"
                    value={targetOddsMin}
                    onChange={(e) => setTargetOddsMin(Number(e.target.value))}
                    className="w-full rounded-lg bg-canvas-midnight border border-border-hairline px-3 py-1.5 text-text-primary"
                  />
                </div>
                <div>
                  <label
                    htmlFor="target-odds-max"
                    className="block font-sans text-text-secondary mb-1"
                  >
                    Kurs docelowy max:
                  </label>
                  <input
                    id="target-odds-max"
                    type="number"
                    step="0.1"
                    min="1.2"
                    max="250"
                    value={targetOddsMax}
                    onChange={(e) => setTargetOddsMax(Number(e.target.value))}
                    className="w-full rounded-lg bg-canvas-midnight border border-border-hairline px-3 py-1.5 text-text-primary"
                  />
                </div>
                <div>
                  <label
                    htmlFor="min-legs-input"
                    className="block font-sans text-text-secondary mb-1"
                  >
                    Min. liczba zdarzeń:
                  </label>
                  <input
                    id="min-legs-input"
                    type="number"
                    min="1"
                    max="8"
                    value={minLegs}
                    onChange={(e) => setMinLegs(Number(e.target.value))}
                    className="w-full rounded-lg bg-canvas-midnight border border-border-hairline px-3 py-1.5 text-text-primary"
                  />
                </div>
                <div>
                  <label
                    htmlFor="max-legs-input"
                    className="block font-sans text-text-secondary mb-1"
                  >
                    Max. liczba zdarzeń:
                  </label>
                  <input
                    id="max-legs-input"
                    type="number"
                    min="1"
                    max="10"
                    value={maxLegs}
                    onChange={(e) => setMaxLegs(Number(e.target.value))}
                    className="w-full rounded-lg bg-canvas-midnight border border-border-hairline px-3 py-1.5 text-text-primary"
                  />
                </div>
              </div>

              {/* Stake PLN Input + Quick PIT Threshold Test */}
              <div className="space-y-1.5">
                <div className="flex items-center justify-between">
                  <label
                    htmlFor="stake-pln-input"
                    className="font-medium text-text-secondary"
                  >
                    Stawka kuponu (PLN):
                  </label>
                  <div className="flex items-center gap-1.5 font-mono">
                    {[100, 500, 1200].map((preset) => (
                      <button
                        key={preset}
                        type="button"
                        onClick={() => handleStakeOrModeChange(preset, bookmakerMode)}
                        className="px-2 py-0.5 rounded bg-surface-elevated text-text-secondary hover:text-signal-emerald border border-border-hairline text-[11px]"
                      >
                        {preset} PLN
                      </button>
                    ))}
                  </div>
                </div>
                <input
                  id="stake-pln-input"
                  type="number"
                  min="1"
                  step="10"
                  value={stake}
                  onChange={(e) =>
                    handleStakeOrModeChange(
                      Math.max(1, Number(e.target.value)),
                      bookmakerMode
                    )
                  }
                  className="w-full rounded-lg bg-canvas-midnight border border-border-hairline px-3 py-2 text-base sm:text-sm text-text-primary font-mono tabular-nums font-bold"
                />
              </div>

              {/* Active Sports Filter in Generator */}
              <div className="space-y-1.5">
                <span className="block font-medium text-text-secondary">
                  Uwzględnij dyscypliny (4 aktywne w v1):
                </span>
                <div className="grid grid-cols-2 gap-2">
                  {ACTIVE_V1_SPORTS.map((sp) => {
                    const checked = generatorSports.includes(sp.slug);
                    return (
                      <button
                        key={sp.slug}
                        type="button"
                        onClick={() => toggleGeneratorSport(sp.slug)}
                        className={`px-2.5 py-1.5 rounded border text-left font-medium transition-colors flex items-center justify-between ${
                          checked
                            ? "bg-surface-elevated border-signal-emerald text-text-primary"
                            : "bg-canvas-midnight border-border-hairline text-text-muted"
                        }`}
                      >
                        <span>{sp.name_pl}</span>
                        <span className="font-mono text-signal-emerald">
                          {checked ? "✓" : ""}
                        </span>
                      </button>
                    );
                  })}
                </div>
              </div>

              {/* Only +EV Toggle */}
              <label className="flex items-center gap-2 cursor-pointer select-none pt-1">
                <input
                  type="checkbox"
                  checked={onlyPlusEvGenerator}
                  onChange={(e) => setOnlyPlusEvGenerator(e.target.checked)}
                  className="rounded border-border-hairline bg-canvas-obsidian text-signal-emerald"
                />
                <span className="text-text-secondary">
                  Wymagaj wyłącznie selekcji z dodatnim EV netto (<span className="font-mono text-signal-emerald">only_plus_ev</span>)
                </span>
              </label>

              {/* Primary CTA Button (LeadBet Brand Blue) */}
              <button
                type="submit"
                disabled={generating}
                className="w-full py-2.5 px-4 rounded-lg bg-brand-blue hover:bg-brand-blue-dark text-white font-semibold text-sm transition-colors duration-150 flex items-center justify-center gap-2 disabled:opacity-50"
              >
                <span>
                  {generating ? "Obliczanie kuponu..." : "Generuj kupon"}
                </span>
              </button>
            </form>

            <div className="pt-2 border-t border-border-hairline flex items-center justify-between text-[11px] text-text-muted">
              <span>Wersja darmowa: analiza pre-match</span>
              <Link href="/cennik" className="text-brand-sky hover:underline font-medium">
                LeadBet Pro →
              </Link>
            </div>

            {/* Proposal Switcher if multiple proposals returned */}
            {proposals.length > 1 && (
              <div className="space-y-1.5 pt-2 border-t border-border-hairline">
                <span className="text-[11px] text-text-muted font-mono">
                  PROPOZYCJE OPTYMALIZATORA ({proposals.length}):
                </span>
                <div className="flex flex-wrap gap-1.5">
                  {proposals.map((prop, idx) => (
                    <button
                      key={prop.id}
                      type="button"
                      onClick={() => setActiveSlip(prop)}
                      className={`px-2.5 py-1 rounded text-xs font-mono tabular-nums border ${
                        activeSlip === prop
                          ? "bg-signal-emerald/20 border-signal-emerald text-signal-emerald font-bold"
                          : "bg-canvas-midnight border-border-hairline text-text-secondary"
                      }`}
                    >
                      #{idx + 1} ({prop.total_odds_gross.toFixed(2)} • P:{" "}
                      {formatPct(prop.joint_probability)})
                    </button>
                  ))}
                </div>
              </div>
            )}
          </div>

          {/* Active Evaluated Slip Card with 1-Click Polish Odds Override & PIT 10% SplitAdvice */}
          <div className="rounded-lg border border-border-hairline bg-surface-slate p-5 space-y-5">
            <div className="flex items-center justify-between border-b border-border-hairline pb-3">
              <div>
                <h3 className="text-base font-bold text-text-primary">
                  Aktywny kupon
                </h3>
                <p className="text-xs text-text-muted">
                  Zmiana kursu przelicza podatek i EV na żywo
                </p>
              </div>
              {evaluating && (
                <span className="text-[11px] font-mono text-brand-sky">
                  Przeliczanie...
                </span>
              )}
            </div>

            {!activeSlip || activeSlip.selections.length === 0 ? (
              <div className="py-8 text-center text-xs text-text-muted space-y-2">
                <p>Brak wybranych pozycji na kuponie.</p>
                <p>Kliknij „Generuj kupon” lub dodaj typ z listy meczów.</p>
              </div>
            ) : (
              <>
                {/* Legs with 1-click Polish odds override */}
                <div className="divide-y divide-border-hairline border border-border-hairline rounded-lg bg-canvas-midnight">
                  {activeSlip.selections.map((sel, idx) => {
                    const legEv = formatEv(sel.ev_net);
                    return (
                      <div
                        key={`${sel.event_id}:${sel.market_key}:${sel.outcome_key}`}
                        className="p-3 space-y-2"
                      >
                        <div className="flex items-start justify-between gap-2">
                          <div>
                            <div className="text-[11px] font-mono text-text-muted">
                              #{idx + 1} • {sel.league_name} ({sel.sport})
                            </div>
                            <div className="text-xs font-bold text-text-primary">
                              {sel.event_name}
                            </div>
                            <div className="text-xs text-signal-emerald font-medium">
                              {sel.market_label}: <span className="font-bold">{sel.outcome_label}</span>
                            </div>
                          </div>
                          <button
                            type="button"
                            onClick={() =>
                              handleRemoveLeg(sel.event_id, sel.market_key, sel.outcome_key)
                            }
                            className="text-xs text-text-muted hover:text-semantic-loss font-mono px-1.5 py-0.5"
                            title="Usuń nogę z kuponu"
                          >
                            ✕
                          </button>
                        </div>

                        {/* Probabilities & 1-click Polish Odds Override Controls */}
                        <div className="pt-2 border-t border-border-hairline/70 flex flex-wrap items-center justify-between gap-2 text-xs font-mono tabular-nums">
                          <div className="space-x-2 text-[11px] text-text-secondary">
                            <span>p_true: {formatPct(sel.p_true)}</span>
                            <span>•</span>
                            <span
                              className={
                                legEv.isPositive ? "text-signal-emerald" : "text-semantic-loss"
                              }
                            >
                              EV: {legEv.text}
                            </span>
                          </div>

                          <div className="flex items-center gap-1">
                            <span className="text-[10px] text-text-muted mr-1">Kurs PL:</span>
                            <button
                              type="button"
                              onClick={() =>
                                handleLegOddsOverride(sel, sel.odds_gross - 0.05)
                              }
                              className="px-2 py-0.5 rounded bg-surface-elevated hover:bg-border-hairline text-text-primary border border-border-hairline font-bold"
                              title="Obniż kurs PL o 0.05 (1-klik ewaluacja)"
                            >
                              -0.05
                            </button>
                            <input
                              type="number"
                              step="0.01"
                              min="1.01"
                              aria-label={`Kurs PL dla ${sel.event_name}`}
                              value={sel.odds_gross}
                              onChange={(e) => {
                                const val = parseFloat(e.target.value);
                                if (!Number.isNaN(val) && val >= 1.01) {
                                  handleLegOddsOverride(sel, val);
                                }
                              }}
                              className="w-16 text-center rounded bg-surface-slate border border-alpha-amber/50 py-0.5 text-alpha-amber font-bold"
                            />
                            <button
                              type="button"
                              onClick={() =>
                                handleLegOddsOverride(sel, sel.odds_gross + 0.05)
                              }
                              className="px-2 py-0.5 rounded bg-surface-elevated hover:bg-border-hairline text-text-primary border border-border-hairline font-bold"
                              title="Podnieś kurs PL o 0.05 (1-klik ewaluacja)"
                            >
                              +0.05
                            </button>
                          </div>
                        </div>
                      </div>
                    );
                  })}
                </div>

                {/* PIT 10% (>2280 PLN) & SplitAdvice Alert */}
                {(activeSlip.pit_10_applies ||
                  activeSlip.potential_payout_gross > 2280) && (
                  <div
                    role="alert"
                    className="rounded-lg border-2 border-alpha-amber bg-alpha-amber/10 p-3.5 space-y-2 text-xs"
                  >
                    <div className="flex items-center justify-between font-mono font-bold text-alpha-amber">
                      <span>▲ OSTRZEŻENIE PODATKOWE PIT 10% (&gt; 2280 PLN)</span>
                      <span className="tabular-nums">
                        -{activeSlip.pit_10_deduction.toFixed(2)} PLN
                      </span>
                    </div>
                    <p className="text-text-primary leading-relaxed">
                      {activeSlip.pit_warning ||
                        "Wygrana przekracza ustawowy próg 2280 PLN. Bukmacher potrąci 10% podatku dochodowego PIT."}
                    </p>
                    {activeSlip.tax_savings_advice && (
                      <div className="rounded bg-canvas-obsidian/80 border border-alpha-amber/40 p-2.5 space-y-1.5 font-mono text-[11px] tabular-nums">
                        <div className="text-signal-emerald font-bold">
                          ✓ REKOMENDACJA OPTYMALIZACJI PODATKOWEJ (SplitAdvice):
                        </div>
                        <p className="font-sans text-text-secondary">
                          {activeSlip.tax_savings_advice.advice_text}
                        </p>
                        <div className="grid grid-cols-3 gap-2 pt-1 text-text-primary">
                          <div>
                            Liczba kuponów:{" "}
                            <span className="font-bold text-alpha-amber">
                              {activeSlip.tax_savings_advice.split_tickets_count}×
                            </span>
                          </div>
                          <div>
                            Stawka/kupon:{" "}
                            <span className="font-bold">
                              {activeSlip.tax_savings_advice.stake_per_ticket.toFixed(2)} PLN
                            </span>
                          </div>
                          <div>
                            Oszczędność PIT:{" "}
                            <span className="font-bold text-signal-emerald">
                              +{activeSlip.tax_savings_advice.net_tax_saved.toFixed(2)} PLN
                            </span>
                          </div>
                        </div>
                        <button
                          type="button"
                          onClick={() =>
                            handleStakeOrModeChange(
                              activeSlip.tax_savings_advice!.stake_per_ticket,
                              bookmakerMode
                            )
                          }
                          className="mt-1 w-full py-1.5 rounded bg-alpha-amber text-canvas-obsidian font-sans font-bold text-xs"
                        >
                          Zastosuj stawkę pojedynczego kuponu (
                          {activeSlip.tax_savings_advice.stake_per_ticket.toFixed(2)} PLN)
                        </button>
                      </div>
                    )}
                  </div>
                )}

                {/* Financial & Probabilistic Summary Grid */}
                <div className="rounded-lg border border-border-hairline bg-canvas-midnight p-3.5 space-y-2.5 font-mono text-xs tabular-nums">
                  <div className="flex justify-between text-text-secondary">
                    <span>Kurs całkowity brutto:</span>
                    <span className="font-bold text-text-primary">
                      {activeSlip.total_odds_gross.toFixed(2)}
                    </span>
                  </div>
                  <div className="flex justify-between text-text-secondary">
                    <span>Mnożnik podatkowy PL:</span>
                    <span
                      className={`font-bold ${
                        activeSlip.tax_multiplier >= 1.0
                          ? "text-signal-emerald"
                          : "text-alpha-amber"
                      }`}
                    >
                      {activeSlip.tax_multiplier.toFixed(2)}× (Kurs netto:{" "}
                      {activeSlip.total_odds_net.toFixed(2)})
                    </span>
                  </div>
                  <div className="flex justify-between text-text-secondary">
                    <span>Łączna szansa wejścia P(kupon):</span>
                    <span className="font-bold text-signal-emerald">
                      {formatPct(activeSlip.joint_probability, 2)}
                    </span>
                  </div>
                  <div className="flex justify-between text-text-secondary">
                    <span>Wartość oczekiwana kuponu (Net EV):</span>
                    <span
                      className={`font-bold ${
                        activeSlip.slip_ev_net >= 0
                          ? "text-signal-emerald"
                          : "text-semantic-loss"
                      }`}
                    >
                      {formatEv(activeSlip.slip_ev_net).text}
                    </span>
                  </div>
                  <div className="flex justify-between text-text-secondary">
                    <span>Ułamek Kelly&apos;ego (0.25× Frac):</span>
                    <span className="text-text-primary">
                      {formatPct(activeSlip.kelly_stake_fraction, 2)} (
                      {activeSlip.kelly_recommended_stake_pln.toFixed(2)} PLN)
                    </span>
                  </div>
                  <div className="pt-2 border-t border-border-hairline flex justify-between items-baseline text-sm">
                    <span className="font-sans font-bold text-text-primary">
                      Potencjalna wygrana netto:
                    </span>
                    <span className="text-lg font-extrabold text-signal-emerald">
                      {activeSlip.potential_payout_net.toFixed(2)} PLN
                    </span>
                  </div>
                </div>

                {/* Save Slip Controls */}
                <div className="space-y-2 pt-2 border-t border-border-hairline">
                  <label
                    htmlFor="slip-name-input"
                    className="block text-xs text-text-secondary font-medium"
                  >
                    Nazwa kuponu do zapisu:
                  </label>
                  <div className="flex gap-2">
                    <input
                      id="slip-name-input"
                      type="text"
                      value={slipName}
                      onChange={(e) => setSlipName(e.target.value)}
                      placeholder="np. AKO Betclic Bez Podatku"
                      className="flex-1 rounded-lg bg-canvas-midnight border border-border-hairline px-3 py-2 text-base sm:text-xs text-text-primary"
                    />
                    <button
                      type="button"
                      disabled={savingSlip}
                      onClick={handleSaveActiveSlip}
                      className="px-4 py-2 rounded-lg bg-signal-emerald hover:bg-signal-emerald-dark text-canvas-obsidian font-bold text-xs shrink-0 transition-colors disabled:opacity-50"
                    >
                      {savingSlip ? "Zapisywanie..." : "Zapisz Kupon"}
                    </button>
                  </div>
                  {savedNotice && (
                    <div className="text-xs font-mono text-signal-emerald flex items-center justify-between pt-1">
                      <span>✓ {savedNotice}</span>
                      <Link href="/kupony" className="underline font-bold">
                        Zobacz Moje Kupony →
                      </Link>
                    </div>
                  )}
                </div>
              </>
            )}
          </div>
        </aside>
      </div>

      {/* Sticky Mobile Jump-to-Slip Bar */}
      <div className="lg:hidden fixed bottom-3 inset-x-3 z-40">
        <a
          href="#kupon-panel"
          className="flex items-center justify-between gap-3 rounded-xl border border-brand-blue/60 bg-surface-slate/95 backdrop-blur-md px-4 py-3 shadow-lg"
        >
          <div className="font-mono text-xs tabular-nums">
            <span className="text-text-muted font-sans">Kupon: </span>
            <span className="font-bold text-text-primary">
              {activeSlip?.selections.length ?? 0} zdarz.
            </span>
            {activeSlip && activeSlip.selections.length > 0 && (
              <span className="text-brand-sky font-bold ml-2">
                AKO {activeSlip.total_odds_gross.toFixed(2)}
              </span>
            )}
          </div>
          <span className="text-xs font-semibold text-brand-sky">
            Przejdź do kuponu ↓
          </span>
        </a>
      </div>
    </div>
  );
}

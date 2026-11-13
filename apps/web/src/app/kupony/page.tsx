"use client";

import React, { useEffect, useState } from "react";
import Link from "next/link";
import {
  CandidateSelection,
  deleteSavedSlip,
  fetchSavedSlips,
  SavedSlipRecord,
} from "../../lib/api";

interface ParsedSelectionItem {
  event_id: string;
  event_name?: string;
  market_key: string;
  outcome_key: string;
  odds: number;
}

function parseSlipSelections(slip: SavedSlipRecord): ParsedSelectionItem[] {
  if (Array.isArray(slip.selections) && slip.selections.length > 0) {
    return slip.selections.map((s: CandidateSelection) => ({
      event_id: s.event_id,
      event_name: s.event_name,
      market_key: s.market_key,
      outcome_key: s.outcome_label || s.outcome_key,
      odds: s.odds_gross,
    }));
  }
  if (typeof slip.selections_json === "string" && slip.selections_json.trim()) {
    try {
      const raw = JSON.parse(slip.selections_json) as Array<{
        event_id?: string;
        market_key?: string;
        outcome_key?: string;
        odds?: number;
      }>;
      if (Array.isArray(raw)) {
        return raw.map((item) => ({
          event_id: item.event_id || "event",
          event_name: item.event_id || "Zdarzenie",
          market_key: item.market_key || "market",
          outcome_key: item.outcome_key || "outcome",
          odds: Number(item.odds ?? 1.5),
        }));
      }
    } catch {
      return [];
    }
  }
  return [];
}

export default function MojeKuponyPage() {
  const [slips, setSlips] = useState<SavedSlipRecord[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [deletingId, setDeletingId] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  const loadSlips = async () => {
    setLoading(true);
    setError(null);
    try {
      const res = await fetchSavedSlips();
      setSlips(res.items || []);
    } catch (err) {
      setError(
        err instanceof Error ? err.message : "Nie udało się pobrać zapisanych kuponów."
      );
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadSlips();
  }, []);

  const handleDelete = async (slipId: string) => {
    setDeletingId(slipId);
    setError(null);
    try {
      await deleteSavedSlip(slipId);
      setSlips((prev) => prev.filter((s) => s.id !== slipId));
    } catch (err) {
      setError(
        err instanceof Error ? err.message : "Błąd podczas usuwania kuponu."
      );
    } finally {
      setDeletingId(null);
    }
  };

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 space-y-8">
      {/* Header */}
      <section className="rounded-xl border border-border-hairline bg-surface-slate p-6 flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div className="space-y-1.5">
          <div className="inline-flex items-center gap-2 px-2.5 py-0.5 rounded bg-canvas-midnight border border-border-hairline text-xs font-mono text-signal-emerald">
            PORTFEL SYMULACJI • ZAPISANE KUPONY AKO
          </div>
          <h1 className="text-2xl sm:text-3xl font-extrabold text-text-primary tracking-tight">
            Moje Zapisane Kupony Matematyczne
          </h1>
          <p className="text-xs sm:text-sm text-text-secondary">
            Przeglądaj zapisane symulacje kuponów, weryfikuj mnożnik podatkowy PL (0.88× / 1.00×),
            status progu PIT 10% (&gt;2280 PLN) oraz zarządzaj listą.
          </p>
        </div>

        <Link
          href="/"
          className="px-4 py-2.5 rounded-lg bg-alpha-amber hover:bg-alpha-amber-dark text-canvas-obsidian font-extrabold text-xs tracking-wide transition-colors shrink-0 text-center"
        >
          + Nowy Kupon w Generatorze
        </Link>
      </section>

      {error && (
        <div className="rounded-lg border border-semantic-loss/40 bg-semantic-loss/10 p-4 text-xs font-mono text-semantic-loss">
          ▼ Błąd: {error}
        </div>
      )}

      {loading ? (
        <div className="rounded-xl border border-border-hairline bg-surface-slate p-10 text-center text-sm font-mono text-text-muted">
          Wczytywanie zapisanych kuponów z bazy LeadBet...
        </div>
      ) : slips.length === 0 ? (
        <div className="rounded-xl border border-border-hairline bg-surface-slate p-10 text-center space-y-3">
          <div className="text-base font-bold text-text-primary">
            Brak zapisanych kuponów
          </div>
          <p className="text-xs text-text-muted max-w-md mx-auto">
            Przejdź do głównego Pulpitu Analitycznego, wygeneruj kupon optymalny i kliknij
            „Zapisz Kupon”, aby zachować go tutaj.
          </p>
          <div className="pt-2">
            <Link
              href="/"
              className="inline-flex items-center gap-2 px-4 py-2 rounded-lg bg-signal-emerald text-canvas-obsidian font-bold text-xs"
            >
              Przejdź do Generatora →
            </Link>
          </div>
        </div>
      ) : (
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {slips.map((slip) => {
            const legs = parseSlipSelections(slip);
            const pitApplies = Boolean(slip.pit_10_applies);
            const evPositive = slip.slip_ev_net >= 0;

            return (
              <article
                key={slip.id}
                className="rounded-xl border border-border-hairline bg-surface-slate p-5 flex flex-col justify-between space-y-4"
              >
                <div className="space-y-4">
                  {/* Card Header */}
                  <div className="flex items-start justify-between gap-3 border-b border-border-hairline pb-3">
                    <div>
                      <div className="flex items-center gap-2">
                        <h2 className="text-base font-bold text-text-primary">
                          {slip.name}
                        </h2>
                        <span className="text-[10px] font-mono uppercase px-2 py-0.5 rounded bg-canvas-midnight text-signal-emerald border border-signal-emerald/30">
                          {slip.bookmaker_key}
                        </span>
                      </div>
                      <p className="text-[11px] font-mono text-text-muted tabular-nums mt-0.5">
                        ID: {slip.id} • Utworzono:{" "}
                        {slip.created_at.replace("T", " ").slice(0, 16)} UTC
                      </p>
                    </div>

                    <button
                      type="button"
                      disabled={deletingId === slip.id}
                      onClick={() => handleDelete(slip.id)}
                      className="px-3 py-1 rounded bg-semantic-loss/15 hover:bg-semantic-loss/25 text-semantic-loss border border-semantic-loss/40 text-xs font-mono font-semibold transition-colors disabled:opacity-50"
                    >
                      {deletingId === slip.id ? "Usuwanie..." : "Usuń"}
                    </button>
                  </div>

                  {/* Legs List */}
                  <div className="space-y-2">
                    <div className="text-xs font-mono text-text-muted">
                      SELEKCJE NA KUPONIE ({legs.length}):
                    </div>
                    <div className="divide-y divide-border-hairline rounded-lg border border-border-hairline bg-canvas-midnight">
                      {legs.map((leg, idx) => (
                        <div
                          key={`${leg.event_id}-${idx}`}
                          className="px-3 py-2 flex items-center justify-between text-xs font-mono tabular-nums"
                        >
                          <div className="truncate pr-2">
                            <span className="text-text-muted mr-1.5">#{idx + 1}</span>
                            <Link
                              href={`/events/${leg.event_id}`}
                              className="font-sans font-semibold text-text-primary hover:text-signal-emerald"
                            >
                              {leg.event_name || leg.event_id}
                            </Link>
                            <span className="text-text-muted ml-2">
                              [{leg.market_key}:{" "}
                              <span className="text-signal-emerald">{leg.outcome_key}</span>]
                            </span>
                          </div>
                          <span className="font-bold text-alpha-amber shrink-0">
                            {leg.odds.toFixed(2)}
                          </span>
                        </div>
                      ))}
                    </div>
                  </div>

                  {/* PIT 10% Badge if applicable */}
                  {pitApplies && (
                    <div className="rounded-lg border border-alpha-amber bg-alpha-amber/10 px-3 py-2 text-xs font-mono text-alpha-amber flex items-center justify-between">
                      <span>▲ Przekroczono próg 2280 PLN (PIT 10% aktywny)</span>
                      <span className="font-bold">Zalecany podział kuponu</span>
                    </div>
                  )}
                </div>

                {/* Financial Footer */}
                <div className="rounded-lg border border-border-hairline bg-canvas-midnight p-3.5 grid grid-cols-2 sm:grid-cols-4 gap-3 font-mono text-xs tabular-nums">
                  <div>
                    <div className="text-[10px] text-text-muted">KURS BRUTTO / NETTO</div>
                    <div className="font-bold text-text-primary">
                      {slip.total_odds_gross.toFixed(2)} / {slip.total_odds_net.toFixed(2)}
                    </div>
                    <div className="text-[10px] text-text-secondary">
                      Podatek: {slip.tax_multiplier.toFixed(2)}×
                    </div>
                  </div>

                  <div>
                    <div className="text-[10px] text-text-muted">SZANSA P(KUPON)</div>
                    <div className="font-bold text-signal-emerald">
                      {(slip.joint_probability * 100).toFixed(2)}%
                    </div>
                    <div className="text-[10px] text-text-secondary">
                      Kelly: {(slip.recommended_kelly_stake_pct * 100).toFixed(2)}%
                    </div>
                  </div>

                  <div>
                    <div className="text-[10px] text-text-muted">WARTOŚĆ EV NETTO</div>
                    <div
                      className={`font-bold ${
                        evPositive ? "text-signal-emerald" : "text-semantic-loss"
                      }`}
                    >
                      {evPositive ? "▲ +" : "▼ "}
                      {(slip.slip_ev_net * 100).toFixed(2)}%
                    </div>
                    <div className="text-[10px] text-text-secondary">
                      Stawka: {slip.stake.toFixed(2)} PLN
                    </div>
                  </div>

                  <div className="text-right">
                    <div className="text-[10px] text-text-muted">WYGRANA NETTO</div>
                    <div className="text-sm font-extrabold text-signal-emerald">
                      {slip.potential_payout_net.toFixed(2)} PLN
                    </div>
                    <div className="text-[10px] text-text-muted">
                      Brutto: {slip.potential_payout_gross.toFixed(2)} PLN
                    </div>
                  </div>
                </div>
              </article>
            );
          })}
        </div>
      )}
    </div>
  );
}

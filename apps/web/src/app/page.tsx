import React from "react";
import type { SportCategory, SplitAdvice } from "@quantkupon/contracts";
import Image from "next/image";

const ACTIVE_SPORTS: Array<Partial<SportCategory> & { icon: string; desc: string }> = [
  {
    slug: "football",
    name_pl: "Piłka nożna",
    active_model: "dixon_coles_xg",
    volatility_tier: "standard",
    icon: "⚽",
    desc: "Bivariate Poisson z wagą 70% xG i korektą niskich wyników (Dixon-Coles τ).",
  },
  {
    slug: "basketball",
    name_pl: "Koszykówka",
    active_model: "pace_possession",
    volatility_tier: "standard",
    icon: "🏀",
    desc: "Tempo posiadań (Pace) i efektywność ORtg/DRtg z rozkładem punktowym Gaussa.",
  },
  {
    slug: "tennis",
    name_pl: "Tenis ziemny",
    active_model: "surface_markov",
    volatility_tier: "standard",
    icon: "🎾",
    desc: "Surface Elo (Hard/Clay/Grass) i łańcuch Markowa punkt → gem → set → mecz.",
  },
  {
    slug: "hockey",
    name_pl: "Hokej na lodzie",
    active_model: "skellam_empty_net",
    volatility_tier: "standard",
    icon: "🏒",
    desc: "Rozkład różnicy goli Skellama (60 min) z poprawką na wycofanego bramkarza (Empty Net).",
  },
];

export default function HomePage() {
  return (
    <div className="space-y-16 pb-20">
      {/* Hero Section */}
      <section className="relative overflow-hidden border-b border-border-hairline bg-canvas-midnight py-16 lg:py-24">
        {/* Subtle background glow */}
        <div className="absolute inset-0 opacity-15 pointer-events-none bg-[radial-gradient(ellipse_at_top,_var(--tw-gradient-stops))] from-signal-emerald via-canvas-midnight to-canvas-obsidian"></div>

        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 relative z-10">
          <div className="grid grid-cols-1 lg:grid-cols-12 gap-12 items-center">
            {/* Left Column: Value Proposition */}
            <div className="lg:col-span-7 space-y-6">
              <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full border border-signal-emerald/30 bg-surface-slate text-xs font-mono text-signal-emerald">
                <span className="w-2 h-2 rounded-full bg-signal-emerald"></span>
                Instytucjonalny Silnik Ilościowy Pre-Match
              </div>

              <h1 className="text-4xl sm:text-5xl font-extrabold tracking-tight text-text-primary leading-tight">
                Matematyczna przewaga nad marżą bukmacherską.
              </h1>

              <p className="text-lg text-text-secondary leading-relaxed max-w-2xl">
                Odrzucamy intuicję na rzecz czystego prawdopodobieństwa. De-vigging algorytmem Shina,
                bayesowska fuzja z rynkiem Pinnacle oraz optymalizator kuponów AKO uwzględniający
                polski podatek obrotowy 12% i próg 2280 PLN.
              </p>

              {/* Action Buttons */}
              <div className="flex flex-wrap gap-4 pt-2">
                <a
                  href="#generator"
                  className="px-6 py-3.5 rounded-lg bg-alpha-amber text-canvas-obsidian font-bold text-sm tracking-wide shadow-lg hover:bg-alpha-amber-dark transition-all transform hover:-translate-y-0.5 flex items-center gap-2"
                >
                  <span>GENERUJ KUPON MATEMATYCZNY</span>
                  <span className="font-mono">→</span>
                </a>
                <a
                  href="#metodologia"
                  className="px-6 py-3.5 rounded-lg bg-surface-slate hover:bg-surface-elevated text-text-primary border border-border-hairline font-medium text-sm transition-all"
                >
                  Poznaj Metodologię
                </a>
              </div>

              {/* Polish Tax Badges */}
              <div className="pt-4 flex flex-wrap items-center gap-6 text-xs text-text-muted font-mono">
                <div className="flex items-center gap-1.5">
                  <span className="text-signal-emerald font-bold">✓</span>
                  <span>Podatek obrotowy 0.88×</span>
                </div>
                <div className="flex items-center gap-1.5">
                  <span className="text-signal-emerald font-bold">✓</span>
                  <span>Promocje Bez Podatku 1.00×</span>
                </div>
                <div className="flex items-center gap-1.5">
                  <span className="text-alpha-amber font-bold">▲</span>
                  <span>Ochrona progu 2280 PLN (PIT 10%)</span>
                </div>
              </div>
            </div>

            {/* Right Column: Hero Visual Asset */}
            <div className="lg:col-span-5">
              <div className="rounded-xl border border-border-hairline bg-surface-slate overflow-hidden shadow-2xl p-4">
                <div className="flex items-center justify-between pb-3 border-b border-border-hairline text-xs font-mono text-text-muted">
                  <span>TERMINAL ANILITYCZNY</span>
                  <span className="text-signal-emerald">STATUS: AKTYWNY</span>
                </div>
                <div className="mt-3 relative rounded-lg overflow-hidden border border-border-hairline/50 aspect-[4/3] bg-canvas-obsidian flex items-center justify-center">
                  <Image
                    src="/hero-quant-analytics.svg"
                    alt="QUANTKUPON Model Matematyczny"
                    width={500}
                    height={375}
                    className="w-full h-full object-contain p-2"
                    priority
                  />
                </div>
                <div className="mt-3 pt-3 border-t border-border-hairline text-[11px] font-mono text-text-muted flex justify-between">
                  <span>Rozkład: Dixon-Coles Bivariate</span>
                  <span className="text-signal-emerald font-tabular">+4.8% Net EV</span>
                </div>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* 4 Active Sports Grid */}
      <section id="kategorie" className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="space-y-4 mb-8">
          <div className="inline-flex items-center gap-1 text-xs font-mono text-signal-emerald uppercase tracking-wider">
            <span>{"// 01. Dyscypliny v1"}</span>
          </div>
          <h2 className="text-2xl sm:text-3xl font-bold text-text-primary tracking-tight">
            Aktywne Modele Probabilistyczne
          </h2>
          <p className="text-text-secondary text-sm max-w-2xl">
            Każda dyscyplina posiada dedykowany model fizyczno-statystyczny kalibrowany na danych historycznych.
            Siatkówka i Tenis stołowy oczekują na premierę w Fazie 2 pod flagą stabilności.
          </p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
          {ACTIVE_SPORTS.map((sport) => (
            <div
              key={sport.slug}
              className="rounded-xl border border-border-hairline bg-surface-slate p-6 hover:border-signal-emerald/50 transition-all hover:-translate-y-1 flex flex-col justify-between space-y-4"
            >
              <div className="space-y-3">
                <div className="flex items-center justify-between">
                  <span className="text-3xl">{sport.icon}</span>
                  <span className="text-[11px] font-mono px-2 py-0.5 rounded bg-surface-elevated text-signal-emerald border border-signal-emerald/20">
                    AKTYWNY v1
                  </span>
                </div>
                <h3 className="text-lg font-bold text-text-primary">{sport.name_pl}</h3>
                <p className="text-xs text-text-secondary leading-relaxed">{sport.desc}</p>
              </div>

              <div className="pt-3 border-t border-border-hairline/60 flex items-center justify-between text-xs font-mono">
                <span className="text-text-muted">Model:</span>
                <span className="text-text-primary font-semibold">{sport.active_model}</span>
              </div>
            </div>
          ))}
        </div>
      </section>

      {/* Polish Tax Engine & Anti-Correlation Preview */}
      <section className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="rounded-2xl border border-border-hairline bg-surface-slate p-8 lg:p-10 space-y-8">
          <div className="max-w-3xl space-y-3">
            <div className="inline-flex items-center gap-1 text-xs font-mono text-signal-emerald uppercase tracking-wider">
              <span>{"// 02. Zgodność z Polskim Prawem i Podatkiem"}</span>
            </div>
            <h2 className="text-2xl sm:text-3xl font-bold text-text-primary tracking-tight">
              Precyzyjna Kalkulacja Podatku Obrotowego i Progu 2280 PLN
            </h2>
            <p className="text-text-secondary text-sm leading-relaxed">
              Legalni bukmacherzy w Polsce podlegają 12% podatkowi od gier (współczynnik 0.88×).
              Nasz silnik uwzględnia promocje bukmacherskie (Betclic, Fortuna, Superbet) oraz
              automatycznie ostrzega przed przekroczeniem progu 2280 PLN, powyżej którego obowiązuje
              dodatkowy podatek ryczałtowy 10% PIT.
            </p>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-6 font-mono">
            <div className="p-5 rounded-xl border border-border-hairline bg-canvas-midnight space-y-2">
              <span className="text-xs text-text-muted uppercase">Standardowy Kupon PL</span>
              <div className="text-2xl font-bold text-text-primary font-tabular">0.88× Payout</div>
              <p className="text-xs text-text-secondary font-sans">
                Ustawowy mnożnik 0.88x uwzględniający 12% podatku od stawki.
              </p>
            </div>

            <div className="p-5 rounded-xl border border-signal-emerald/30 bg-canvas-midnight space-y-2">
              <span className="text-xs text-signal-emerald uppercase font-semibold">
                Promocja „Bez Podatku”
              </span>
              <div className="text-2xl font-bold text-signal-emerald font-tabular">1.00× Payout</div>
              <p className="text-xs text-text-secondary font-sans">
                Kwalifikowane zakłady AKO z zachowaniem pełnego zysku brutto.
              </p>
            </div>

            <div className="p-5 rounded-xl border border-alpha-amber/30 bg-canvas-midnight space-y-2">
              <span className="text-xs text-alpha-amber uppercase font-semibold">
                Próg PIT (&gt; 2280 PLN)
              </span>
              <div className="text-2xl font-bold text-alpha-amber font-tabular">Podział Kuponu</div>
              <p className="text-xs text-text-secondary font-sans">
                Rekomendacja podziału stawki na dwa mniejsze kupony w celu ominięcia 10% PIT.
              </p>
            </div>
          </div>
        </div>
      </section>
    </div>
  );
}

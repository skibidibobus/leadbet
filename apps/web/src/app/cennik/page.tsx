import React from "react";
import Link from "next/link";

const PLANS = [
  {
    name: "Free",
    price: "0 PLN",
    period: "na zawsze",
    description: "Podstawowa analiza pre-match i kalkulator polskiego podatku.",
    features: [
      "4 dyscypliny pre-match (piłka, koszykówka, tenis, hokej)",
      "Porównanie p_model vs rynek referencyjny",
      "Kalkulator podatku 12% (0.88× / 1.00×) i alert PIT > 2280 PLN",
      "Generator kuponów do 2 zdarzeń",
    ],
    cta: "Korzystaj bezpłatnie",
    href: "/",
    highlighted: false,
  },
  {
    name: "LeadBet Pro",
    price: "29 PLN",
    period: "/ mies. (lub 249 PLN / rok)",
    description: "Pełny optymalizator kuponów, podział PIT i alerty zmian kursów.",
    features: [
      "Generator kuponów do 10 zdarzeń z filtrem +EV",
      "Automatyczny kalkulator podziału stawki (SplitAdvice PIT 10%)",
      "Nielimitowane zapisywanie i archiwum kuponów",
      "Powiadomienia o zmianach kursów pre-match (2×/dzień)",
    ],
    cta: "Wybierz Pro (wkrótce)",
    href: "/",
    highlighted: true,
  },
  {
    name: "API & Dane",
    price: "99 PLN",
    period: "/ mies.",
    description: "Dostęp programistyczny do macierzy prawdopodobieństw i audytu CLV.",
    features: [
      "Endpointy REST JSON (/api/v1/events, /breakdown, /calibration)",
      "Eksport historycznych próbek Brier Score i CLV",
      "Własne wagi fuzji bayesowskiej i de-vigging Shina",
      "Faktura VAT za oprogramowanie analityczne",
    ],
    cta: "Dokumentacja API",
    href: "/kalibracja",
    highlighted: false,
  },
] as const;

export default function CennikPage() {
  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 space-y-8">
      <div className="flex flex-col sm:flex-row sm:items-baseline sm:justify-between gap-2 border-b border-border-hairline pb-4">
        <div>
          <h1 className="text-xl font-bold tracking-tight text-text-primary">
            Plany dostępu do oprogramowania LeadBet
          </h1>
          <p className="text-xs text-text-muted mt-1">
            Model SaaS — opłata wyłącznie za narzędzie analityczne i kalkulator podatkowy (faktura VAT, brak prowizji i afiliacji bukmacherskiej).
          </p>
        </div>
        <Link
          href="/"
          className="text-xs font-medium text-brand-sky hover:underline shrink-0"
        >
          ← Wróć do pulpitu
        </Link>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        {PLANS.map((plan) => (
          <section
            key={plan.name}
            className={`rounded-lg border p-6 flex flex-col justify-between space-y-6 ${
              plan.highlighted
                ? "border-brand-blue bg-surface-slate"
                : "border-border-hairline bg-surface-slate"
            }`}
          >
            <div className="space-y-4">
              <div className="flex items-baseline justify-between gap-2">
                <h2 className="text-base font-bold text-text-primary">
                  {plan.name}
                </h2>
                {plan.highlighted && (
                  <span className="text-[11px] font-medium text-brand-sky">
                    Rekomendowany
                  </span>
                )}
              </div>

              <div className="flex items-baseline gap-1.5">
                <span className="text-2xl font-bold font-mono tabular-nums text-text-primary">
                  {plan.price}
                </span>
                <span className="text-xs text-text-muted">{plan.period}</span>
              </div>

              <p className="text-xs text-text-secondary leading-relaxed">
                {plan.description}
              </p>

              <ul className="space-y-2 pt-2 border-t border-border-hairline text-xs text-text-secondary">
                {plan.features.map((feat) => (
                  <li key={feat} className="flex items-start gap-2">
                    <span className="text-brand-sky font-mono shrink-0">✓</span>
                    <span>{feat}</span>
                  </li>
                ))}
              </ul>
            </div>

            <Link
              href={plan.href}
              className={`block w-full text-center py-2.5 px-4 rounded-lg text-xs font-semibold transition-colors duration-150 ${
                plan.highlighted
                  ? "bg-brand-blue hover:bg-brand-blue-dark text-white"
                  : "bg-surface-elevated hover:bg-border-hairline text-text-primary border border-border-hairline"
              }`}
            >
              {plan.cta}
            </Link>
          </section>
        ))}
      </div>
    </div>
  );
}

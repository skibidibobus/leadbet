import React from "react";
import Link from "next/link";

export function Footer() {
  return (
    <footer className="border-t border-border-hairline bg-surface-slate text-text-muted text-xs py-8 mt-auto">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 space-y-4">
        <div className="flex flex-col md:flex-row items-start md:items-center justify-between gap-4 border-b border-border-hairline pb-4">
          <div className="flex items-center space-x-2.5">
            <span className="inline-flex items-center justify-center w-7 h-7 rounded-full bg-semantic-loss/20 text-semantic-loss font-mono font-bold border border-semantic-loss/40 shrink-0">
              18+
            </span>
            <div className="space-y-0.5">
              <p className="font-semibold text-text-primary">
                Narzędzie wyłącznie matematyczno-analityczne. Brak rekomendacji gry.
              </p>
              <p className="text-[11px] text-text-secondary">
                Serwis przeznaczony wyłącznie dla osób pełnoletnich (18+). Zgodność z RODO oraz ustawą o grach hazardowych.
              </p>
            </div>
          </div>

          <div className="flex flex-wrap items-center gap-4 text-text-secondary font-medium">
            <Link href="/" className="hover:text-signal-emerald transition-colors">
              Pulpit
            </Link>
            <span>•</span>
            <Link href="/kalibracja" className="hover:text-signal-emerald transition-colors">
              Kalibracja i CLV
            </Link>
            <span>•</span>
            <Link href="/kupony" className="hover:text-signal-emerald transition-colors">
              Moje Kupony
            </Link>
          </div>
        </div>

        <p className="leading-relaxed text-[11px] text-text-muted">
          LeadBet jest niezależnym narzędziem analitycznym pre-match i nie prowadzi działalności bukmacherskiej
          ani nie przyjmuje zakładów wzajemnych. Wszelkie wartości prawdopodobieństwa, EV oraz symulacje podatku
          obrotowego (12% / 0.88×) i PIT 10% powyżej 2280 PLN mają charakter wyłącznie informacyjny.
        </p>

        <div className="pt-2 flex flex-col sm:flex-row items-center justify-between gap-2 text-[11px] text-text-muted/80 font-mono tabular-nums">
          <span>© {new Date().getFullYear()} LeadBet</span>
          <span>18+ • RODO • Analiza pre-match</span>
        </div>
      </div>
    </footer>
  );
}

export default Footer;

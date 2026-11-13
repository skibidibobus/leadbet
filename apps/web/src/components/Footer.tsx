import React from "react";
import Link from "next/link";

export function Footer() {
  return (
    <footer className="border-t border-border-hairline bg-surface-slate text-text-muted text-xs py-6 mt-auto">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
        <div className="flex items-center gap-3">
          <span className="inline-flex items-center justify-center px-1.5 py-0.5 rounded bg-surface-elevated text-text-secondary font-mono text-[11px] font-semibold border border-border-hairline shrink-0">
            18+
          </span>
          <p className="text-[11px] text-text-muted leading-snug">
            LeadBet — narzędzie analityczne pre-match. Nie przyjmuje zakładów ani nie udziela rekomendacji gry. Zgodność z RODO.
          </p>
        </div>

        <div className="flex flex-wrap items-center gap-4 text-[11px] text-text-secondary shrink-0">
          <Link href="/kalibracja" className="hover:text-brand-sky transition-colors">
            Kalibracja
          </Link>
          <Link href="/kupony" className="hover:text-brand-sky transition-colors">
            Kupony
          </Link>
          <Link href="/cennik" className="hover:text-brand-sky transition-colors">
            Cennik Pro
          </Link>
          <span className="text-text-muted/70 font-mono tabular-nums">
            © {new Date().getFullYear()} LeadBet
          </span>
        </div>
      </div>
    </footer>
  );
}

export default Footer;

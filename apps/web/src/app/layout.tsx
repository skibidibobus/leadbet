import type { Metadata } from "next";
import { Inter, JetBrains_Mono } from "next/font/google";
import "../styles/globals.css";

const inter = Inter({
  subsets: ["latin", "latin-ext"],
  variable: "--font-sans",
  display: "swap",
});

const jetbrainsMono = JetBrains_Mono({
  subsets: ["latin", "latin-ext"],
  variable: "--font-mono",
  display: "swap",
});

export const metadata: Metadata = {
  title: "QUANTKUPON — Matematyczna Analiza Kursów i Generator Kuponów",
  description:
    "Instytucjonalna analityka pre-match, modele probabilistyczne (Dixon-Coles, Pace, Markov, Skellam), de-vigging Shin/Power i optymalizator kuponów z uwzględnieniem polskiego podatku 12%.",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="pl" className={`dark ${inter.variable} ${jetbrainsMono.variable}`}>
      <body className="bg-canvas-obsidian text-text-primary antialiased min-h-screen flex flex-col selection:bg-signal-emerald selection:text-canvas-obsidian">
        {/* Top Institutional Header */}
        <header className="border-b border-border-hairline bg-surface-slate/80 backdrop-blur-md sticky top-0 z-50">
          <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 h-16 flex items-center justify-between">
            <div className="flex items-center space-x-3">
              <span className="font-mono text-xl font-bold tracking-tight text-text-primary flex items-center gap-1.5">
                <span className="text-signal-emerald">QUANT</span>KUPON
                <span className="text-xs px-2 py-0.5 rounded bg-surface-elevated text-text-muted border border-border-hairline font-sans font-medium">
                  v1.0 BETA
                </span>
              </span>
            </div>
            <nav className="hidden md:flex items-center space-x-6 text-sm font-medium text-text-secondary">
              <a href="#kategorie" className="hover:text-signal-emerald transition-colors">
                Dyscypliny
              </a>
              <a href="#metodologia" className="hover:text-signal-emerald transition-colors">
                Metodologia
              </a>
              <a href="#generator" className="hover:text-signal-emerald transition-colors">
                Generator Kuponów
              </a>
              <a href="#kalibracja" className="hover:text-signal-emerald transition-colors">
                Audyt Modeli
              </a>
            </nav>
            <div className="flex items-center space-x-3">
              <span className="text-xs font-mono px-2.5 py-1 rounded border border-signal-emerald/30 bg-signal-emerald/10 text-signal-emerald flex items-center gap-1 font-semibold">
                <span className="w-1.5 h-1.5 rounded-full bg-signal-emerald animate-pulse"></span>
                0.88× / Bez Podatku
              </span>
            </div>
          </div>
        </header>

        {/* Main Content Area */}
        <main className="flex-grow">{children}</main>

        {/* Statutory Legal & Responsible Gaming Footer */}
        <footer className="border-t border-border-hairline bg-surface-slate text-text-muted text-xs py-8">
          <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 space-y-4">
            <div className="flex flex-col md:flex-row items-center justify-between gap-4 border-b border-border-hairline pb-4">
              <div className="flex items-center space-x-2">
                <span className="inline-flex items-center justify-center w-7 h-7 rounded-full bg-semantic-loss/20 text-semantic-loss font-bold border border-semantic-loss/40">
                  18+
                </span>
                <span className="font-medium text-text-secondary">
                  Serwis przeznaczony wyłącznie dla osób pełnoletnich (18+).
                </span>
              </div>
              <div className="flex items-center space-x-4 text-text-muted">
                <span>Ustawa o grach hazardowych z dnia 19 listopada 2009 r.</span>
                <span>•</span>
                <span>Zgodność RODO</span>
              </div>
            </div>
            <p className="leading-relaxed text-[11px] text-text-muted/80">
              QUANTKUPON jest niezależnym narzędziem analityczno-statystycznym i nie prowadzi działalności
              bukmacherskiej ani nie przyjmuje zakładów wzajemnych. Prezentowane wskaźniki (+EV, prawdopodobieństwa
              Poissona/Skellama/Markowa, kursy referencyjne) stanowią wyłącznie symulacje matematyczne oparte o dane historyczne
              i nie stanowią gwarancji wygranej. Graj odpowiedzialnie. Zakłady bukmacherskie wiążą się z ryzykiem utraty kapitału.
            </p>
            <div className="pt-2 text-center text-text-muted text-[11px]">
              © {new Date().getFullYear()} QUANTKUPON. Wszelkie prawa zastrzeżone.
            </div>
          </div>
        </footer>
      </body>
    </html>
  );
}

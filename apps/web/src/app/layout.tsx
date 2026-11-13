import type { Metadata } from "next";
import { Inter, JetBrains_Mono } from "next/font/google";
import "../styles/globals.css";
import { Navbar } from "../components/Navbar";
import { Footer } from "../components/Footer";

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
  title: "LeadBet — Matematyczna Analiza Kursów i Generator Kuponów",
  description:
    "Narzędzie analityczne pre-match. Modele probabilistyczne, de-vigging i optymalizator kuponów z uwzględnieniem polskiego podatku 12% oraz PIT 10% (>2280 PLN).",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="pl" className={`dark ${inter.variable} ${jetbrainsMono.variable}`}>
      <body className="bg-canvas-obsidian text-text-primary antialiased min-h-screen flex flex-col selection:bg-signal-emerald selection:text-canvas-obsidian">
        <Navbar />
        <main className="flex-grow">{children}</main>
        <Footer />
      </body>
    </html>
  );
}

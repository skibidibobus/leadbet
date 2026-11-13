"use client";

import React from "react";
import Link from "next/link";
import { usePathname } from "next/navigation";

const NAV_ITEMS = [
  { href: "/", label: "Pulpit" },
  { href: "/kalibracja", label: "Kalibracja" },
  { href: "/kupony", label: "Moje Kupony" },
] as const;

export function Navbar() {
  const pathname = usePathname();

  return (
    <header className="border-b border-border-hairline bg-surface-slate/90 backdrop-blur-md sticky top-0 z-50">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 h-14 flex items-center justify-between gap-4">
        <div className="flex items-center">
          <Link
            href="/"
            className="font-sans text-xl font-bold tracking-tight"
          >
            <span className="text-sky-400">Lead</span><span className="text-blue-500">Bet</span>
          </Link>
        </div>

        <nav
          aria-label="Główna nawigacja"
          className="flex items-center space-x-1 sm:space-x-4 text-xs sm:text-sm font-medium"
        >
          {NAV_ITEMS.map((item) => {
            const isActive =
              item.href === "/"
                ? pathname === "/" || pathname.startsWith("/events")
                : pathname.startsWith(item.href);

            return (
              <Link
                key={item.href}
                href={item.href}
                className={`px-2.5 sm:px-3 py-1.5 rounded-md whitespace-nowrap transition-colors ${
                  isActive
                    ? "bg-surface-elevated text-signal-emerald border border-signal-emerald/30 font-semibold"
                    : "text-text-secondary hover:text-text-primary hover:bg-surface-elevated/60"
                }`}
              >
                {item.label}
              </Link>
            );
          })}
        </nav>

        <div className="hidden md:block text-xs font-mono text-text-muted tabular-nums">
          Pre-match • PL 0.88× / 1.00×
        </div>
      </div>
    </header>
  );
}

export default Navbar;

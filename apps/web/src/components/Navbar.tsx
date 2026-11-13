"use client";

import React from "react";
import Link from "next/link";
import { usePathname } from "next/navigation";

const NAV_ITEMS = [
  { href: "/", label: "Pulpit" },
  { href: "/kalibracja", label: "Kalibracja" },
  { href: "/kupony", label: "Kupony" },
  { href: "/cennik", label: "Cennik" },
] as const;

export function Navbar() {
  const pathname = usePathname();

  return (
    <header className="border-b border-border-hairline bg-surface-slate sticky top-0 z-50">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 h-14 flex items-center justify-between gap-3">
        <Link
          href="/"
          className="inline-flex items-center gap-2.5 font-sans text-lg font-bold tracking-tight shrink-0"
        >
          <svg
            width="24"
            height="24"
            viewBox="0 0 24 24"
            fill="none"
            aria-hidden="true"
            className="shrink-0"
          >
            <rect
              x="1"
              y="1"
              width="22"
              height="22"
              rx="6"
              fill="#0F1624"
              stroke="#2563EB"
              strokeWidth="1.5"
            />
            <path
              d="M6.5 16.5V12.5M12 16.5V9.5M17.5 16.5V6.5"
              stroke="#38BDF8"
              strokeWidth="2"
              strokeLinecap="round"
            />
          </svg>
          <span>
            <span className="text-brand-sky">Lead</span>
            <span className="text-blue-500">Bet</span>
          </span>
        </Link>

        <nav
          aria-label="Główna nawigacja"
          className="flex items-center space-x-1 sm:space-x-2 text-xs sm:text-sm font-medium"
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
                className={`px-2.5 sm:px-3 py-1.5 rounded-lg whitespace-nowrap transition-colors duration-150 ${
                  isActive
                    ? "bg-surface-elevated text-brand-sky border border-brand-blue/50 font-semibold"
                    : "text-text-secondary hover:text-text-primary hover:bg-surface-elevated/60"
                }`}
              >
                {item.label}
              </Link>
            );
          })}
        </nav>

        <div className="hidden md:block text-xs text-text-muted tabular-nums">
          Pre-match • Podatek PL <span className="font-mono">0.88× / 1.00×</span>
        </div>
      </div>
    </header>
  );
}

export default Navbar;

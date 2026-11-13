# LeadBet

**Pre-match Quantitative Odds Analyzer, Combinatorial Slip Optimizer & Polish Tax Engine**

[![Live Demo](https://img.shields.io/badge/Live%20Demo-GitHub%20Pages-2563EB?style=flat-square)](https://skibidibobus.github.io/leadbet/)
[![FastAPI](https://img.shields.io/badge/Backend-FastAPI%20%2B%20Python-0F172A?style=flat-square)](apps/api)
[![Next.js](https://img.shields.io/badge/Frontend-Next.js%2015%20%2B%20TypeScript-0F172A?style=flat-square)](apps/web)
[![License: MIT](https://img.shields.io/badge/License-MIT-334155?style=flat-square)](LICENSE)

**Live Demo:** https://skibidibobus.github.io/leadbet/

---

## Overview

**LeadBet** is a full-stack, pre-match sports analytics platform built as a TypeScript + Python monorepo. It compares statistical sport-model probabilities (`p_model`) against de-vigged sharp market benchmarks (`p_sharp`), fuses them via Bayesian weighting (`p_true`), and solves for optimal multi-leg combinations while factoring in **Polish statutory betting taxation** (12% turnover tax `0.88×`, promotional `1.00×` exemptions, and 10% PIT threshold above `2280.00 PLN` with automated ticket-splitting advice).

The system is architected for **0 PLN infrastructure cost**: pre-match odds refresh runs 2×/day via GitHub Actions, the FastAPI engine serves validated JSON endpoints, and the Next.js App Router frontend builds as a static export on GitHub Pages with deterministic offline fallback.

---

## Key Engineering Highlights

- **Quantitative Modeling Engine (`packages/quant-engine`):**
  - Sport-specific pre-match models: **Dixon-Coles** (Football), **Pace / ORtg–DRtg** (Basketball), **Surface Markov Elo** (Tennis), **Skellam 60m** (Ice Hockey).
  - **Shin & Power De-vigging** to strip bookmaker overround from reference odds.
  - **Bayesian Probability Fusion** combining model priors and sharp market consensus.
  - **Beam-Search Combinatorial Optimizer** maximizing joint probability $P(\text{slip})$ within target odds bounds, enforcing an **Anti-Correlation Guard** (max 1 leg per `event_id`) and **Quarter-Kelly (`0.25×`, 5% cap)** sizing.
  - **Model Calibration Audit:** Brier Score, Brier Skill Score, Log-Loss, Expected Calibration Error (ECE), and Closing Line Value (CLV) reliability bins.
- **Polish Tax & Promo Engine (`packages/bookmaker-adapters`):**
  - Exact evaluation of `standard_088` (`0.88×`), `betclic_tax_free` (`>= 2` legs, `>= 1.20`), `fortuna_promo` (`>= 3` legs, `>= 1.30`), and `superbet_boost` (`>= 3` legs, `>= 1.25`).
  - Automatic detection of the `2280.00 PLN` 10% PIT threshold with optimal `SplitAdvice` ticket-splitting calculation.
- **Responsive Product UI & SaaS Architecture (`apps/web`):**
  - Next.js 15 App Router + React 19 + TypeScript + Tailwind CSS.
  - Mobile-first outcome cards, sticky quick-jump slip bar, real-time 1-click odds override (`POST /api/v1/slips/evaluate`), SVG calibration charts, and `/cennik` SaaS tiering.
- **Automated CI/CD & Ingestion (`.github/workflows`):**
  - `deploy_pages.yml`: `pnpm` monorepo static export (`output: "export"`) deployed to GitHub Pages on push to `main`.
  - `ingest_prematch.yml`: Scheduled 2×/day (`08:00` & `16:00 UTC`) pre-match ingestion pipeline.

---

## Monorepo Architecture

| Package / App | Stack | Responsibility |
|---|---|---|
| `apps/web` | Next.js 15, React 19, TypeScript, Tailwind | Responsive dashboard, match breakdown, calibration charts, saved slips, `/cennik` |
| `apps/api` | FastAPI, Pydantic v2, Uvicorn | REST API (`/api/v1/*`), CORS allowlisting, pre-match `cron_ingest.py` |
| `packages/quant-engine` | Python, NumPy, SciPy | Sport models, Shin de-vigging, Bayesian fusion, Kelly sizing, Beam-Search optimizer |
| `packages/bookmaker-adapters` | Python, Pydantic, HTTPX | Polish tax/PIT engine (`PolishTaxEngine`), fixture & The Odds API adapters |
| `packages/contracts` | OpenAPI 3.1, PostgreSQL DDL, TypeScript | Shared API contracts and Neon PostgreSQL schema |

---

## Local Setup & Verification

### Backend & Quantitative Engine

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -e packages/quant-engine -e packages/bookmaker-adapters
pip install fastapi uvicorn httpx pytest pydantic

# Run unit & API integration tests
PYTHONPATH=apps/api:packages/quant-engine:packages/bookmaker-adapters \
  pytest packages/ apps/api/ -v

# Start FastAPI server (port 8000)
PYTHONPATH=apps/api:packages/quant-engine:packages/bookmaker-adapters \
  uvicorn src.main:app --reload --port 8000
```

### Frontend

```bash
pnpm install --frozen-lockfile
pnpm --filter @quantkupon/web type-check
pnpm --filter @quantkupon/web dev
```

---

## Compliance & Security

- **Analytical Scope Only:** LeadBet does not accept bets, process payments, or publish betting recommendations or affiliate links.
- **Regulatory Alignment:** Designed for 18+ users with RODO/GDPR notice and statutory Polish tax transparency.
- **Security:** Zero hardcoded secrets (`.env.example` template only), explicit `CORS_ORIGINS` allowlist, and strict Pydantic input validation. See [SECURITY.md](SECURITY.md).

---

## License

[MIT](LICENSE)

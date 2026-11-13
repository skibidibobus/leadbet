# Project: QUANTKUPON

## Architecture
- **Monorepo Layout**: Modular TypeScript and Python monorepo (`apps/web`, `apps/api`, `packages/quant-engine`, `packages/bookmaker-adapters`, `packages/contracts`).
- **Data Flow**:
  1. Data Ingestors (`packages/bookmaker-adapters`) fetch pre-match data (2x daily) or load offline mock fixtures.
  2. Mathematical models & de-vigging (`packages/quant-engine`) compute probabilities ($p_{\text{model}}$, $p_{\text{sharp}}$, $p_{\text{true}}$).
  3. `PolishTaxEngine` applies statutory 12% tax (0.88x), promotional zero-tax rates, and 10% PIT threshold (> 2280 PLN).
  4. Pre-calculated predictions and odds snapshots are stored in Neon PostgreSQL.
  5. FastAPI backend (`apps/api`) exposes REST endpoints (`/categories`, `/events`, `/slips/generate`, `/slips/evaluate`, `/calibration/metrics`, `/slips/saved`) conforming to OpenAPI 3.1.
  6. Next.js frontend (`apps/web`) renders pre-match tables via SSR from Neon PostgreSQL (<200ms) and invokes FastAPI for dynamic coupon optimization and 1-click odds overrides.
  7. User authentication via Auth.js (Google OAuth + Magic Link Email) with mandatory 18+ age declaration and RODO compliance.

## Feature Inventory
| # | Feature | Description | Milestone | Source |
|---|---------|-------------|-----------|--------|
| 1 | Monorepo layout | Modular structure (`apps/web`, `apps/api`, `packages/quant-engine`, `packages/bookmaker-adapters`, `packages/contracts`) | M1 | `PLAN_PROJEKTU.md` §5.1, `ORIGINAL_REQUEST.md` R1 |
| 2 | Neon PostgreSQL schema | 9 tables covering users, sessions, sports, leagues, events, competitor ratings, odds snapshots, predictions, saved slips | M1 | `PLAN_PROJEKTU.md` §5.2, `ORIGINAL_REQUEST.md` R1 |
| 3 | OpenAPI 3.1 contract | Standardized endpoints for categories, events, breakdown, slip generation, evaluation, saved slips, calibration + TS types | M1 | `PLAN_PROJEKTU.md` §5.3, `ORIGINAL_REQUEST.md` R1 |
| 4 | De-vigging (Shin method) | Market margin removal modeling informed trader fraction $z \in (0,1)$ | M2 | `PLAN_PROJEKTU.md` §3 (Etap 1), `ORIGINAL_REQUEST.md` R2 |
| 5 | De-vigging (Power method) | Solves $\sum (1/O_i)^c = 1$ via Brent numerical solver | M2 | `PLAN_PROJEKTU.md` §3 (Etap 1), `ORIGINAL_REQUEST.md` R2 |
| 6 | De-vigging (Multiplicative) | Proportional normalization baseline | M2 | `PLAN_PROJEKTU.md` §3 (Etap 1), `ORIGINAL_REQUEST.md` R2 |
| 7 | Football Dixon-Coles model | Bivariate Poisson with low-score correlation $\tau$ and 70% xG / 30% goal weighting | M2 | `PLAN_PROJEKTU.md` §3 (Etap 2A), `ORIGINAL_REQUEST.md` R2 |
| 8 | Basketball Pace model | Possession-based pace modeling with Gaussian point spread and total | M2 | `PLAN_PROJEKTU.md` §3 (Etap 2B), `ORIGINAL_REQUEST.md` R2 |
| 9 | Tennis Markov chain | Surface Elo (Hard/Clay/Grass) + point-to-game-to-set-to-match dynamic programming | M2 | `PLAN_PROJEKTU.md` §3 (Etap 2D), `ORIGINAL_REQUEST.md` R2 |
| 10 | Hockey Skellam model | Skellam goal difference distribution (60') with Empty Net correction | M2 | `PLAN_PROJEKTU.md` §3 (Etap 2E), `ORIGINAL_REQUEST.md` R2 |
| 11 | Phase 2 sports feature flag | Volleyball and Table Tennis models implemented behind `ENABLE_PHASE2_SPORTS=false` | M2 | `PLAN_PROJEKTU.md` §1.2, §3 (Etap 2C, 2F), `ORIGINAL_REQUEST.md` R2 |
| 12 | Table Tennis Volatility Guard | Dynamic shrinkage towards sharp market and `#F59E0B` alert when $\sigma$ is high | M2 | `PLAN_PROJEKTU.md` §3 (Etap 2F), `ORIGINAL_REQUEST.md` R2 |
| 13 | Bayesian market fusion | Blends statistical model $p_{\text{model}}$ with sharp consensus $p_{\text{sharp}}$ | M2 | `PLAN_PROJEKTU.md` §3 (Etap 3), `ORIGINAL_REQUEST.md` R2 |
| 14 | 12% Turnover tax | Applies statutory 0.88x payout multiplier under Polish Gambling Act | M2 | `PLAN_PROJEKTU.md` §2.2, `ORIGINAL_REQUEST.md` R2 |
| 15 | Promotional Zero-Tax profiles | Applies $k_{\text{tax}} = 1.00$ for qualifying accumulator bets (Betclic, Fortuna, Superbet) | M2 | `PLAN_PROJEKTU.md` §2.2, `ORIGINAL_REQUEST.md` R2 |
| 16 | 10% PIT threshold (> 2280 PLN) | Automatically deducts 10% of total payout if potential winning $> 2280$ PLN | M2 | `PLAN_PROJEKTU.md` §2.2, `ORIGINAL_REQUEST.md` R2 |
| 17 | Mathematical coupon splitting advice | Calculates tax savings from splitting high-payout bets into 2 slips to avoid 10% PIT | M2 | `PLAN_PROJEKTU.md` §2.2, `ORIGINAL_REQUEST.md` R2 |
| 18 | Fractional Kelly criterion | Recommends bankroll percentage using $\gamma = 0.25$ capped at 5% | M2 | `PLAN_PROJEKTU.md` §3 (Etap 4), `ORIGINAL_REQUEST.md` R2 |
| 19 | Quantitative audit metrics | Calculates Brier Score, Log-Loss, and Closing Line Value (CLV) | M2 | `PLAN_PROJEKTU.md` §3 (Etap 3), §5.3, `ORIGINAL_REQUEST.md` R2 |
| 20 | 0 PLN pre-match cron | Ingests data 2x/day within free quotas (The Odds API, football-data, nba_api, NHL) | M3 | `PLAN_PROJEKTU.md` §2.1, §5.1, `ORIGINAL_REQUEST.md` R3 |
| 21 | Deterministic offline test mode | Mock adapters and pre-recorded JSON fixtures for offline development | M3 | `ORIGINAL_REQUEST.md` R3, Acceptance Criteria |
| 22 | Combinatorial coupon generator | Maximizes $P(\text{coupon})$ within user odds range $[O_{\min}, O_{\max}]$ | M4 | `PLAN_PROJEKTU.md` §4, `ORIGINAL_REQUEST.md` R4 |
| 23 | Anti-Correlation Guard | Enforces $\le 1$ selection per match fixture to prevent invalid probability multiplication | M4 | `PLAN_PROJEKTU.md` §4, `ORIGINAL_REQUEST.md` R4 |
| 24 | Explicit Net EV & +EV filter | Shows exact Net EV with red `▼` if negative; optional toggle to enforce only $+EV$ | M4 | `PLAN_PROJEKTU.md` §4, `ORIGINAL_REQUEST.md` R4 |
| 25 | 1-Click Polish bookmaker override | Allows user to type exact STS/Fortuna/Betclic odds with live recalculation | M4 | `PLAN_PROJEKTU.md` §2.1, §4, `ORIGINAL_REQUEST.md` R4 |
| 26 | 60-30-10 Design system | Obsidian `#0B0F19`, Slate `#131C2E`, Emerald `#10B981`, Amber `#F59E0B` | M5 | `design/STYL_I_GRAFIKI.md`, `PLAN_PROJEKTU.md` §6, `ORIGINAL_REQUEST.md` R5 |
| 27 | Rule "Never Color Alone" | EV and odds indicators always combine color with sign (`+/-`) and arrow (`▲/▼`) | M5 | `design/STYL_I_GRAFIKI.md` §2, `ORIGINAL_REQUEST.md` R5 |
| 28 | Auth & Legal 18+ / RODO gate | Google OAuth / Email login with mandatory 18+ declaration and GDPR controls | M5 | `PLAN_PROJEKTU.md` §8, §5.2, `ORIGINAL_REQUEST.md` R5 |
| 29 | Cloudflare Pages + Render Free hosting setup | Static/SSR frontend on Cloudflare Pages, API on Render Free (~1 min cold start) | M1 | `PLAN_PROJEKTU.md` §5.1, `ORIGINAL_REQUEST.md` R1, R5 |

## Milestones
| # | Name | Scope | Dependencies | Status |
|---|------|-------|-------------|--------|
| M1 | Monorepo Setup, Neon DB Schema & OpenAPI Contracts | Setup pnpm monorepo layout, define Neon PostgreSQL schema (9 tables), author OpenAPI 3.1 specification, and generate TypeScript types | none | DONE |
| M2 | Quantitative Mathematical Core & Polish Tax Engine | Pure Python quantitative algorithms (Shin, Power, Multiplicative de-vigging; 4 active sport models: Football Dixon-Coles, Basketball Pace, Tennis Markov, Hockey Skellam; Phase 2 sports behind flag; Bayesian fusion; Kelly criterion; calibration metrics; PolishTaxEngine with 0.88x, promotional zero-tax, 10% PIT threshold, ticket splitting) | M1 | IN_PROGRESS (06dba7ed-d236-4916-a9c0-84afd92f1b3b) |
| M3 | Pre-Match Data Ingestion & Deterministic Offline Pipeline | Free endpoint ingestors within quotas, deterministic mock adapters, local JSON fixtures, batch calculations, Neon persistence, and GitHub Actions cron workflow | M1, M2 | PLANNED |
| M4 | Combinatorial Coupon Optimizer & FastAPI Service | Beam-search coupon solver maximizing $P(\text{coupon})$ with Anti-Correlation Guard, FastAPI endpoints (`/categories`, `/events`, `/events/{id}/breakdown`, `/slips/generate`, `/slips/evaluate`, `/calibration/metrics`, `/slips/saved`) | M1, M2, M3 | PLANNED |
| M5 | Next.js Frontend with 60-30-10 Design System & Auth.js | Next.js 15+ App Router, 60-30-10 tokens, Hero section (tactile image + SVG math cards), 4 sport category views, interactive coupon generator UI with 1-click odds override, Auth.js Google/email login, `/moje-kupony`, and 18+/RODO legal footer | M1, M3, M4 | PLANNED |
| M6 | Final Milestone: 100% E2E Test Suite Pass & Adversarial Hardening | Phase 1: Pass 100% of E2E test suite (Tiers 1-4). Phase 2: Adversarial coverage hardening (Tier 5) with Challenger/Worker/Reviewer loop | M1, M2, M3, M4, M5, TEST_READY.md | PLANNED |

## Interface Contracts
### `packages/contracts` ↔ `apps/api` (FastAPI) & `apps/web` (Next.js)
- **Specification Path**: `packages/contracts/openapi.yaml` (OpenAPI 3.1.0).
- **TypeScript Types**: `packages/contracts/src/types.ts` generated via `openapi-typescript`.
- **Database DDL**: `packages/contracts/schema.sql` (PostgreSQL 15+ compatible for Neon).
- **Core Endpoints**:
  - `GET /api/v1/categories`: returns active sports with fixture counts.
  - `GET /api/v1/events`: filtered pre-match events with odds and model probabilities.
  - `GET /api/v1/events/{id}/breakdown`: full mathematical breakdown (Poisson matrix, Markov states, factual factors).
  - `POST /api/v1/slips/generate`: combinatorial optimization solver returning top coupons.
  - `POST /api/v1/slips/evaluate`: instant live recalculation upon user odds override or stake change.
  - `GET /api/v1/calibration/metrics`: Brier scores, Log-Loss, and CLV metrics.
  - `GET /api/v1/slips/saved`, `POST /api/v1/slips/saved`, `DELETE /api/v1/slips/saved/{id}`: user coupon storage.

### `packages/quant-engine` ↔ `packages/bookmaker-adapters` & `apps/api`
- **De-vigging**: `devig_shin(odds: list[float]) -> list[float]`, `devig_power(odds: list[float]) -> tuple[list[float], float]`, `devig_multiplicative(odds: list[float]) -> list[float]`. Invariant: $\sum p_i = 1.0 \pm 10^{-6}$.
- **PolishTaxEngine**:
  - `calculate_net_payout(stake: float, total_odds_gross: float, tax_multiplier: float = 0.88) -> TaxEvaluationResult`
  - Returns `TaxEvaluationResult`: `total_odds_net: float`, `potential_payout_gross: float`, `potential_payout_net: float`, `pit_10_applies: bool`, `pit_10_deduction: float`, `split_advice: Optional[SplitAdvice]`.
  - Invariant: If `potential_payout_gross <= 2280.00`, `pit_10_deduction == 0.0`. If `potential_payout_gross > 2280.00`, `potential_payout_net == 0.90 * potential_payout_gross`.
- **Sport Models**:
  - `FootballModel.predict(match_context: MatchContext) -> FootballPredictionResult` (Dixon-Coles bivariate Poisson with xG weighting).
  - `BasketballModel.predict(match_context: MatchContext) -> BasketballPredictionResult` (Possession pace and normal distributions).
  - `TennisModel.predict(match_context: MatchContext) -> TennisPredictionResult` (Surface Elo + Markov chain).
  - `HockeyModel.predict(match_context: MatchContext) -> HockeyPredictionResult` (Skellam + empty net adjustment).
  - Invariant: all probability outputs satisfy $\sum p_i = 1.0 \pm 10^{-5}$ and $p_i \in [0, 1]$.
- **Coupon Solver**:
  - `SlipOptimizer.optimize(pool: list[CandidateLeg], config: SolverConfig) -> list[OptimizedCoupon]`.
  - Invariant: strictly $\le 1$ leg per `event_id` in any coupon.

## Code Layout
```text
bukmacherka/
├── apps/
│   ├── web/                              # Next.js 15+ frontend application
│   │   ├── src/
│   │   │   ├── app/                      # App router routes (/, /analiza/[sport], /generator-kuponow, etc.)
│   │   │   ├── components/               # 60-30-10 UI components (Hero, OddsTable, CouponSlip, etc.)
│   │   │   ├── lib/                      # Neon DB SSR client, API client, Auth.js config
│   │   │   └── styles/                   # Tailwind design tokens (#0B0F19, #131C2E, #10B981, #F59E0B)
│   │   ├── public/                       # Design assets (hero image, SVGs)
│   │   └── package.json
│   └── api/                              # FastAPI Python application
│       ├── src/
│       │   ├── api/                      # Route handlers (/categories, /events, /slips, etc.)
│       │   ├── services/                 # Slip generator & evaluation services
│       │   ├── db/                       # Neon PostgreSQL connection & repositories
│       │   └── main.py                   # FastAPI app entry point
│       ├── tests/                        # FastAPI endpoint unit & integration tests
│       └── pyproject.toml
├── packages/
│   ├── quant-engine/                     # Pure Python quantitative math library
│   │   ├── quant_engine/
│   │   │   ├── core/                     # devig.py, bayesian.py, kelly.py, calibration.py
│   │   │   ├── sports/                   # football.py, basketball.py, tennis.py, hockey.py, volleyball.py, table_tennis.py
│   │   │   └── optimizer/                # solver.py (Max-Szansa beam search, Anti-Correlation Guard)
│   │   ├── tests/                        # Mathematical invariant unit tests (sum P = 1.0, convergence)
│   │   └── pyproject.toml
│   ├── bookmaker-adapters/               # Feed adapters, tax engine, offline fixtures
│   │   ├── bookmaker_adapters/
│   │   │   ├── tax/                      # polish_tax_engine.py
│   │   │   ├── feeds/                    # the_odds_api.py, football_data.py, nba_api.py, nhl.py, tennis.py
│   │   │   ├── mock/                     # mock_adapter.py (deterministic offline provider)
│   │   │   └── fixtures/                 # Local pre-recorded JSON fixture files
│   │   ├── tests/                        # Tax math tests, mock ingestion tests
│   │   └── pyproject.toml
│   └── contracts/                        # Schemas, specifications, and types
│       ├── openapi.yaml                  # Authoritative OpenAPI 3.1 specification
│       ├── schema.sql                    # Complete Neon PostgreSQL DDL schema
│       ├── src/types.ts                  # Generated TypeScript interfaces
│       └── package.json
├── .github/
│   └── workflows/
│       ├── ingest-cron.yml               # 2x daily data ingestion & model update workflow
│       └── test.yml                      # CI test runner
├── tests/
│   ├── e2e/                              # Playwright UI & full system integration tests
│   └── fixtures/                         # Monorepo shared test fixtures
├── package.json                          # Root pnpm monorepo workspace configuration
├── pnpm-workspace.yaml
├── PROJECT.md                            # Single source of truth project index
└── ORIGINAL_REQUEST.md                   # Verbatim user requirements
```

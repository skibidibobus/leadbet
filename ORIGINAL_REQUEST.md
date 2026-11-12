# Original User Request

## Initial Request — 2026-11-12T20:20:43Z

Implementation of the QUANTKUPON sports betting mathematical analysis and coupon generator platform across all phases (Phases 0–3), executed in coordination between Gemini 4 Hydrogen and Gemini 4 Argon models according to the ownership matrix and phases in PLAN_PROJEKTU.md.

Working directory: /Users/hubertlichorobiec/Antigravity projects/bukmacherka
Integrity mode: development

References:
- Architecture & implementation plan: `PLAN_PROJEKTU.md`
- Visual style & design tokens (60-30-10): `design/STYL_I_GRAFIKI.md`
- Visual assets: `design/examples/`

## Requirements

### R1. Architecture, Monorepo Setup, Neon Database Schema & API Contracts
Set up the monorepo structure (`apps/web`, `apps/api`, `packages/quant-engine`, `packages/bookmaker-adapters`, `packages/contracts`). Define the complete Neon PostgreSQL database schema (sports categories, leagues, events, competitor ratings, odds snapshots, model predictions, users, accounts, sessions, saved slips). Specify the OpenAPI 3.1 contract (`packages/contracts/openapi.yaml`) covering all endpoints and generate TypeScript type definitions.

### R2. Quantitative Mathematical Core & Polish Tax Engine
Implement `packages/quant-engine` and `packages/bookmaker-adapters`:
- De-vigging methods (Shin method, Power method, Multiplicative method) and Bayesian fusion with sharp market consensus.
- Category prediction models for 4 active v1 sports: Football (Dixon-Coles + xG), Basketball (Pace/Possession + Spread/Totals), Tennis (Markov chain + Surface Elo), Ice Hockey (Skellam + Empty Net correction). Volleyball and Table Tennis models implemented behind the feature flag `ENABLE_PHASE2_SPORTS=false`.
- `PolishTaxEngine` handling statutory 12% turnover tax (0.88x multiplier), bookmaker promotion rules (Betclic "Bez Podatku", Fortuna, Superbet), and the 10% PIT threshold on winnings exceeding 2280 PLN.
- Fractional Kelly criterion (gamma = 0.25, cap at 5%) and calibration metrics (Brier Score, Log-Loss, CLV).

### R3. Pre-Match Data Ingestion & GitHub Actions Cron Pipeline
Implement budget-aware data ingestors for free endpoints (The Odds API within free tier limits, football-data, nba_api, NHL API, tennis archives) updating 2x daily via GitHub Actions schedule and persisting predictions into Neon PostgreSQL, with mock adapters and deterministic test fixtures for offline development and testing.

### R4. Combinatorial Coupon Optimizer & FastAPI Service
Implement the coupon generator solver that maximizes mathematical win probability P(coupon) within a user-specified odds range (with explicit net EV display, Anti-Correlation Guard enforcing at most one selection per match, and optional +EV filter). Provide FastAPI endpoints (`/slips/generate`, `/slips/evaluate` for instant 1-click bookmaker odds overrides, `/categories`, `/events`, `/calibration/metrics`, `/slips/saved`).

### R5. Next.js Frontend with 60-30-10 Design System & Cloudflare Pages Compatibility
Implement the responsive web application (`apps/web`):
- Design system applying 60-30-10 "Quant Slate & Emerald Terminal" palette (`#0B0F19` slate, `#131C2E` card surfaces, `#10B981` emerald EV, `#F59E0B` amber CTA/volatility).
- Hero section combining tactile background image (`hero-quant-analytics.jpg`) with crisp interactive SVG math cards (`hero-quant-analytics.svg`).
- Navigation and views for the 4 active v1 categories (Football, Basketball, Tennis, Hockey) with odds tables and Poisson/Markov breakdown sheets.
- Interactive Coupon Generator supporting target odds ranges, risk profiles, 1-click Polish bookmaker odds overrides, tax factor recalculation, and 2280 PLN tax threshold warnings.
- Auth.js authentication (Google OAuth + email), saved slips panel (`/moje-kupony`), and strict 18+ compliance & RODO disclaimer notices.

## Acceptance Criteria

### Verification & Testing
- [ ] Offline test mode: all test suites execute and pass deterministically using local mock adapters and test fixtures without requiring live external API keys.
- [ ] Automated mathematical invariant tests: probability distributions sum to 1.0 ($\sum P = 1.0$), de-vigging solvers converge within tolerance, and PolishTaxEngine correctly calculates 0.88x net payout, promotional zero-tax rates, and the 10% PIT deduction for winnings over 2280 PLN.
- [ ] API contract validation: the OpenAPI 3.1 schema validates with zero errors, and TypeScript types match backend response schemas.
- [ ] Backend test suite: FastAPI endpoints (`/categories`, `/events`, `/slips/generate`, `/slips/evaluate`, `/calibration/metrics`) return valid responses with test fixtures.
- [ ] Frontend build & tests: Next.js project compiles cleanly with zero TypeScript errors, conforms to 60-30-10 palette rules, and passes UI integration tests for slip generation, 1-click odds overrides, and 18+/RODO disclaimers.

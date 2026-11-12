# QUANTKUPON — Test Infrastructure & Deterministic Offline E2E Test Suite Specification

**Document Version:** 1.0.0  
**Target Repository:** `bukmacherka`  
**Milestone:** E2E-M1 (Test Infrastructure & Runner Harness)  
**Authoritative Sources:** `ORIGINAL_REQUEST.md`, `PLAN_PROJEKTU.md`, `PROJECT.md`, `design/STYL_I_GRAFIKI.md`, `.agents/teamwork/sub_orch_e2e_testing/SCOPE.md`

---

## 1. Test Philosophy & Core Invariants

The QUANTKUPON platform testing infrastructure is designed around four foundational architectural principles:

1. **Opaque-Box Testing:**  
   Tests exercise the system exclusively through public, stable interface boundaries: public package APIs (`packages/quant-engine`, `packages/bookmaker-adapters`), REST endpoints (`apps/api`), relational database tables and foreign key constraints (`packages/contracts/schema.sql`), and UI interaction states (`apps/web`). Tests do not inspect or mock internal private implementation variables.

2. **Requirement-Driven Verification:**  
   Every single test case across all tiers maps directly to a numbered requirement in `ORIGINAL_REQUEST.md` (R1–R5), an architectural specification in `PLAN_PROJEKTU.md`, or a visual design token in `design/STYL_I_GRAFIKI.md`. Facade tests that pass without verifying genuine system behavior are strictly prohibited.

3. **Deterministic Offline Execution (`OFFLINE_MODE=true`):**  
   The entire test suite executes and passes 100% offline without live external API keys (The Odds API, football-data, nba_api, NHL API, tennis archives). Socket connections to non-loopback external hosts are intercepted and blocked at the runtime level. All tests run against pre-recorded, deterministic JSON fixtures located in `tests/fixtures/`, with fixed pseudorandom seeds (`random.seed(42)`, `np.random.seed(42)`).

4. **Progressive Testability & Hierarchical Tiers:**  
   The test suite is organized into four hierarchical tiers:
   - **Tier 1 (Feature Coverage):** $\ge 145$ isolated feature tests ($\ge 5$ tests per feature across all 29 features).
   - **Tier 2 (Boundary & Corner Cases):** $\ge 145$ boundary tests ($\ge 5$ per feature covering edge tolerances, 2280 PLN borders, zero/negative stakes, extreme odds, etc.).
   - **Tier 3 (Cross-Feature Combinations):** $\ge 29$ pairwise integration tests verifying multi-module handoffs.
   - **Tier 4 (Real-World Scenarios):** $\ge 15$ end-to-end user application workload scenarios.
   Unimplemented tiers are classified as `PENDING` during early milestones without triggering false CI failures, while ensuring that 100% of discovered tests must pass with exit code `0`.

---

## 2. Complete 29-Feature Inventory & Coverage Specification

| # | Category | Feature Name | Requirements Source | Category-Partition Boundaries & Equivalence Classes | Mathematical Invariants & Tolerances ($\epsilon$) | Error Behavior | Tier Assignments |
|---|---|---|---|---|---|---|---|
| **1** | Architecture | Monorepo layout | `PLAN_PROJEKTU.md` §5.1, `ORIGINAL_REQUEST.md` R1 | Valid: 5 modular directories (`apps/web`, `apps/api`, `packages/quant-engine`, `packages/bookmaker-adapters`, `packages/contracts`).<br>Boundary: zero circular imports.<br>Invalid: cross-import from quant-engine into apps/api. | Cyclic dependency count $= 0$. Pure math core has zero network/I/O dependencies. | Module resolution error on circular or unauthorized import. | Tier 1 (5), Tier 2 (5), Tier 3 |
| **2** | Database | Neon PostgreSQL schema | `PLAN_PROJEKTU.md` §5.2, `contracts/schema.sql` | Valid: 9 tables (`users`, `accounts`, `sessions`, `sports_categories`, `leagues`, `events`, `competitor_ratings`, `odds_snapshots`, `model_predictions`, `saved_slips`).<br>Boundary: exact foreign keys with `ON DELETE CASCADE`.<br>Invalid: invalid probabilities ($p < 0$ or $p > 1$), negative odds. | Referential integrity strictly enforced.<br>Check constraints: $p \in [0, 1]$, $O > 1.0$. | Database raises `IntegrityError` (check or foreign key violation). | Tier 1 (5), Tier 2 (5), Tier 3 |
| **3** | API | OpenAPI 3.1 contract | `PLAN_PROJEKTU.md` §5.3, `contracts/openapi.yaml` | Valid: Endpoints `/categories`, `/events`, `/events/{id}/breakdown`, `/slips/generate`, `/slips/evaluate`, `/calibration/metrics`, `/slips/saved`.<br>Boundary: Typed TypeScript interfaces match Pydantic response models. | OpenAPI 3.1.0 schema validation error count $= 0$. | Returns HTTP 400, 404, or 422 with `{ "detail": [...] }`. | Tier 1 (5), Tier 2 (5), Tier 3 |
| **4** | Quant Core | De-vigging (Shin method) | `PLAN_PROJEKTU.md` §3 (Etap 1), `ORIGINAL_REQUEST.md` R2 | Valid: Odds vector $O \in \mathbb{R}_{>1}^k$ ($k \ge 2$), overround $M \in (0.01, 0.25)$.<br>Classes: Balanced 2-way, 3-way, heavy favorite/longshot ($1.02$ vs $35.0$).<br>Invalid: $O_i \le 1.0$, empty vector. | $\sum p_{\text{shin}, i} = 1.0 \pm 10^{-6}$.<br>Insider fraction $z \in (0, 1)$ solved via Brent root-finding ($\le 10^{-7}$).<br>Monotonicity: $O_i < O_j \implies p_i > p_j$. | Fallback to Power method if Brent solver fails; `ValueError` on $O_i \le 1.0$. | Tier 1 (5), Tier 2 (5), Tier 3, Tier 4 |
| **5** | Quant Core | De-vigging (Power method) | `PLAN_PROJEKTU.md` §3 (Etap 1), `ORIGINAL_REQUEST.md` R2 | Valid: Solves $\sum (1/O_i)^c = 1$ over $c \in [0.5, 2.0]$.<br>Boundary: Fair market where $\sum 1/O_i = 1.0 \implies c = 1.0$.<br>Invalid: $O_i \le 1.0$. | $\sum (1/O_i)^c = 1.0 \pm 10^{-6}$.<br>Brent root residual $|f(c)| \le 10^{-7}$.<br>$p_i = (1/O_i)^c \in (0, 1)$. | Fallback to Multiplicative method if no root in $[0.5, 2.0]$; `ValueError` on invalid odds. | Tier 1 (5), Tier 2 (5), Tier 3 |
| **6** | Quant Core | De-vigging (Multiplicative) | `PLAN_PROJEKTU.md` §3 (Etap 1), `ORIGINAL_REQUEST.md` R2 | Valid: Proportional normalization $p_i = \frac{1/O_i}{\sum 1/O_j}$.<br>Boundary: $k=2, 3, 10$.<br>Invalid: Empty odds list, non-positive odds. | $\sum p_{\text{mult}, i} = 1.0 \pm 10^{-6}$.<br>$p_{\text{mult}, i} > 0$ strictly. | `ValueError` on empty odds or odds $\le 1.0$. | Tier 1 (5), Tier 2 (5), Tier 3 |
| **7** | Quant Core | Football Dixon-Coles model | `PLAN_PROJEKTU.md` §3 (Etap 2A), `ORIGINAL_REQUEST.md` R2 | Valid: Intensities $\lambda, \mu > 0$, correlation $\rho \in (-0.25, 0.25)$, 70% xG / 30% goal weighting.<br>Classes: High-scoring, defensive, lopsided.<br>Boundary: Scoreless history ($0$ goals, $0$ xG). | $\sum_{x=0}^8 \sum_{y=0}^8 P(x, y) + P_{\text{tail}} = 1.0 \pm 10^{-5}$.<br>$P(1)+P(X)+P(2) = 1.0 \pm 10^{-5}$.<br>Positivity: $P(x, y) \ge 0$. | Clamps $\lambda, \mu \ge 10^{-4}$ to prevent division by zero; clamps $\tau(x, y) \ge 0$. | Tier 1 (5), Tier 2 (5), Tier 3, Tier 4 |
| **8** | Quant Core | Basketball Pace model | `PLAN_PROJEKTU.md` §3 (Etap 2B), `ORIGINAL_REQUEST.md` R2 | Valid: Match pace $(\text{Pace}_A \cdot \text{Pace}_B)/\text{Pace}_{\text{lg}}$, ORtg, DRtg, HCA, rest penalties.<br>Classes: Fast-paced, defensive battle, blowout.<br>Boundary: Spread line $= 0.0$, Total line $= 220.5$. | Moneyline: $P(\text{Home})+P(\text{Away}) = 1.0 \pm 10^{-5}$.<br>Spread CDF: $P(D>L)+P(D\le L) = 1.0 \pm 10^{-5}$.<br>Totals CDF: $P(T>T_0)+P(T\le T_0) = 1.0 \pm 10^{-5}$. | Variance floor $\sigma \ge 1.0$; `ValueError` on non-positive pace. | Tier 1 (5), Tier 2 (5), Tier 3, Tier 4 |
| **9** | Quant Core | Tennis Markov chain | `PLAN_PROJEKTU.md` §3 (Etap 2D), `ORIGINAL_REQUEST.md` R2 | Valid: Surface Elo (Hard, Clay, Grass), $p_A, p_B \in (0, 1)$, Bo3/Bo5 formats.<br>Classes: Dominant server ($p=0.72$), returner rally ($p=0.58$).<br>Boundary: Deuce state ($40:40$), $p=0.50$. | Absorbing deuce formula: $\frac{p^2}{p^2 + (1-p)^2}$.<br>Match sum: $\sum P(\text{score}) = 1.0 \pm 10^{-5}$.<br>Game complementary: $P_{\text{game}}(p)+P_{\text{game}}(1-p) = 1.0 \pm 10^{-6}$. | Clamps point probabilities to $[0.01, 0.99]$ to avoid zero division in deuce denominator. | Tier 1 (5), Tier 2 (5), Tier 3, Tier 4 |
| **10** | Quant Core | Hockey Skellam model | `PLAN_PROJEKTU.md` §3 (Etap 2E), `ORIGINAL_REQUEST.md` R2 | Valid: Goal rates $\lambda, \mu > 0$, regulation 60' Skellam distribution, Empty Net correction ($\kappa_{\text{EN}} = 3.2\times$).<br>Classes: Standard NHL match, defensive slugfest.<br>Boundary: Trailing by 1-2 goals at $t \ge 58'$. | Regulation 1X2 sum: $P(1)+P(X)+P(2) = 1.0 \pm 10^{-5}$.<br>Empty net monotonicity: $P_{\text{EN}}(\text{Over 5.5}) > P_{\text{raw}}(\text{Over 5.5})$.<br>OT ML sum: $P(\text{Home})+P(\text{Away}) = 1.0 \pm 10^{-5}$. | Suppresses empty net boost if trailing team is shorthanded (penalty kill); `ValueError` on $\lambda \le 0$. | Tier 1 (5), Tier 2 (5), Tier 3, Tier 4 |
| **11** | Quant Core | Phase 2 sports feature flag | `PLAN_PROJEKTU.md` §1.2, §3 (Etap 2C, 2F), `ORIGINAL_REQUEST.md` R2 | Valid: `ENABLE_PHASE2_SPORTS=false` (default) vs `true`.<br>Classes: Flag `false` hides Volleyball and Table Tennis in UI/API; flag `true` activates all 6 sports. | When flag is `false`, exactly 4 sports returned in active categories; zero Phase 2 selections in coupon solver. | Requesting Phase 2 sport when flag is `false` returns HTTP 400 or drops category. | Tier 1 (5), Tier 2 (5), Tier 3, Tier 4 |
| **12** | Quant Core | Table Tennis Volatility Guard | `PLAN_PROJEKTU.md` §3 (Etap 2F), `ORIGINAL_REQUEST.md` R2 | Valid: Glicko-2 $\sigma_i$, RD, match count $N_{\text{h2h}}$.<br>Standard: $\sigma \le 0.06, RD \le 120 \implies w=0.30$.<br>Guard Active: $\sigma > 0.06$ or $RD > 120$ or $N < 5 \implies w_{\text{shrink}} = \max(0.10, w \cdot \frac{0.06}{\sigma})$. | Fused prob: $p_{\text{true}} = w_{\text{shrink}} p_{\text{model}} + (1-w_{\text{shrink}}) p_{\text{sharp}} \in [0, 1]$.<br>As $\sigma \to \infty$, $w \to 0.10$. | Default prior $RD=350, \sigma=0.09$, activates Guard, and emits Amber `#F59E0B` alert in UI. | Tier 1 (5), Tier 2 (5), Tier 3, Tier 4 |
| **13** | Quant Core | Bayesian market fusion | `PLAN_PROJEKTU.md` §3 (Etap 3), `ORIGINAL_REQUEST.md` R2 | Valid: Blends $p_{\text{model}}$ and $p_{\text{sharp}}$ using sport weights (Football $0.45$, Basketball $0.40$, Tennis $0.40$, Hockey $0.35$).<br>Boundary: $w=0.0$ (pure sharp), $w=1.0$ (pure model). | Convex combination: $\min(p_{\text{m}}, p_{\text{s}}) \le p_{\text{true}} \le \max(p_{\text{m}}, p_{\text{s}})$.<br>Sum: $\sum p_{\text{true}, i} = 1.0 \pm 10^{-5}$. | If $p_{\text{sharp}}$ missing, fallback to $p_{\text{model}}$; if $p_{\text{model}}$ missing, fallback to $p_{\text{sharp}}$. | Tier 1 (5), Tier 2 (5), Tier 3 |
| **14** | Tax Engine | 12% Turnover tax | `PLAN_PROJEKTU.md` §2.2, `ORIGINAL_REQUEST.md` R2 | Valid: Stake $S > 0$, Gross odds $O_{\text{gross}} \ge 1.00$.<br>Statutory tax multiplier: $k_{\text{tax}} = 0.88$.<br>Boundary: $S=0.01$ PLN, $O=1.00$.<br>Invalid: $S \le 0, O < 1.00$. | Net odds: $O_{\text{net}} = 0.88 \cdot O_{\text{gross}}$.<br>Net payout (for $W \le 2280$ PLN): $\text{round}(S \cdot 0.88 \cdot O_{\text{gross}}, 2)$.<br>Tolerance: $\pm 0.02$ PLN. | Rejects stake $\le 0$ or odds $< 1.00$ with `ValueError`. | Tier 1 (5), Tier 2 (5), Tier 3, Tier 4 |
| **15** | Tax Engine | Promotional Zero-Tax profiles | `PLAN_PROJEKTU.md` §2.2, `ORIGINAL_REQUEST.md` R2 | Valid: Betclic ($\ge 2$ legs, every leg $O_i \ge 1.20 \implies k_{\text{tax}}=1.00$); Fortuna ($\ge 3$ legs, every leg $O_i \ge 1.30 \implies k_{\text{tax}}=1.00$).<br>Boundary: Betclic $[1.20, 1.20] \implies 1.00$; leg $1.19 \implies 0.88$. | If qualifying: $k_{\text{tax}} = 1.000000$.<br>If non-qualifying: automatic fallback to $k_{\text{tax}} = 0.880000$. | Reverts to 0.88x with informational warning if criteria not met. | Tier 1 (5), Tier 2 (5), Tier 3, Tier 4 |
| **16** | Tax Engine | 10% PIT threshold (> 2280 PLN) | `PLAN_PROJEKTU.md` §2.2, `ORIGINAL_REQUEST.md` R2 | Valid: Payout $W = S \cdot k_{\text{tax}} \cdot O_{\text{gross}}$.<br>Exact Boundary: $W = 2280.00$ PLN $\implies$ PIT $= 0.00$ PLN.<br>Exceeded: $W = 2280.01$ PLN $\implies$ 10% PIT on full payout ($228.00$ PLN deduction). | If $W \le 2280.00$: `pit_10_applies=False`, `pit_10_deduction=0.00`.<br>If $W > 2280.00$: `pit_10_applies=True`, `deduction=round(0.10*W, 2)`, `net=round(0.90*W, 2)`. | Triggers `SplitAdvice` recommendation whenever $W > 2280.00$ PLN. | Tier 1 (5), Tier 2 (5), Tier 3, Tier 4 |
| **17** | Tax Engine | Mathematical ticket splitting advice | `PLAN_PROJEKTU.md` §2.2, `ORIGINAL_REQUEST.md` R2 | Valid: Total payout $W > 2280.00$ PLN.<br>Effective split ($2280 < W \le 4560$ PLN): Split into 2 tickets ($S/2$), eliminating 10% PIT completely.<br>Ineffective 2-way split ($W > 4560$ PLN): advises $k = \lceil W / 2280 \rceil$ tickets. | Split stake: $S/2$.<br>Tax saved: $\text{round}(0.10 \cdot W, 2)$ when $W/2 \le 2280.00$.<br>Combined payout $= W$. | Returns `None` or zero savings if payout $\le 2280.00$ PLN. | Tier 1 (5), Tier 2 (5), Tier 3, Tier 4 |
| **18** | Staking | Fractional Kelly criterion | `PLAN_PROJEKTU.md` §3 (Etap 4), `ORIGINAL_REQUEST.md` R2 | Valid: Quarter-Kelly ($\gamma = 0.25$) on net edge $b_{\text{net}} = O_{\text{gross}} \cdot k_{\text{tax}} - 1$.<br>Classes: Negative EV ($f^* = 0.0$), positive EV ($0 < f^* \le 0.05$), extreme edge ($f^* = 0.05$ capped). | Range: $0.0 \le f^* \le 0.0500$ strictly.<br>If $\text{EV} \le 0$, $f^* = 0.0$.<br>Safety ceiling: exactly $0.05$ (5% max bankroll). | If $b_{\text{net}} \le 0$ (odds after tax $\le 1.0$), return $f^* = 0.0$. | Tier 1 (5), Tier 2 (5), Tier 3, Tier 4 |
| **19** | Calibration | Quantitative audit metrics | `PLAN_PROJEKTU.md` §3 (Etap 3), §5.3, `ORIGINAL_REQUEST.md` R2 | Valid: Brier Score $\frac{1}{N}\sum(p_i-y_i)^2$, Log-Loss, and Closing Line Value $\text{CLV} = O_{\text{bet}} / O_{\text{closing}} - 1$.<br>Boundary: Perfect predictions (Brier $=0$), 50/50 baseline (Brier $=0.25$). | $0.0 \le \text{Brier} \le 1.0$.<br>$\text{Log-Loss} \ge 0.0$.<br>Probabilities clipped to $[\epsilon, 1-\epsilon]$ ($\epsilon = 10^{-15}$). | Raises `ValueError` if dataset is empty. | Tier 1 (5), Tier 2 (5), Tier 3, Tier 4 |
| **20** | Ingestion | 0 PLN pre-match cron | `PLAN_PROJEKTU.md` §2.1, §5.1, `ORIGINAL_REQUEST.md` R3 | Valid: 2x daily schedule (06:00, 14:00 UTC) within free quotas (The Odds API $\le 500$/month $\approx 8$/day).<br>Boundary: Daily quota limits strictly observed. | Rate limits never exceeded; upsert operations into Neon DB are idempotent. | On upstream HTTP 429 or timeout, gracefully logs error and preserves existing snapshot. | Tier 1 (5), Tier 2 (5), Tier 3, Tier 4 |
| **21** | Ingestion | Deterministic offline test mode | `ORIGINAL_REQUEST.md` R3, Acceptance Criteria | Valid: `OFFLINE_MODE=true` environment, local JSON fixtures in `tests/fixtures/`, loopback socket allowlist.<br>Boundary: Zero external HTTP/socket requests permitted. | 100% reproducible test execution across runs. External socket calls raise `RuntimeError`. | Aborts test immediately if unmocked external network I/O is attempted. | Tier 1 (5), Tier 2 (5), Tier 3, Tier 4 |
| **22** | Optimizer | Combinatorial coupon generator | `PLAN_PROJEKTU.md` §4, `ORIGINAL_REQUEST.md` R4 | Valid: Maximizes joint probability $P(\text{coupon}) = \prod p_{\text{true}, i}$ subject to $[O_{\min}, O_{\max}]$ and leg count $[n_{\min}, n_{\max}]$.<br>Classes: Feasible vs Infeasible target range. | For every generated coupon: $O_{\min} \le O_{\text{gross}} \le O_{\max}$.<br>$n_{\min} \le \text{len} \le n_{\max}$.<br>$P(\text{coupon}) \in (0, 1)$. | If infeasible, returns `{"coupons": []}` with recommendations to widen odds range. | Tier 1 (5), Tier 2 (5), Tier 3, Tier 4 |
| **23** | Optimizer | Anti-Correlation Guard | `PLAN_PROJEKTU.md` §4, `ORIGINAL_REQUEST.md` R4 | Valid: Strictly enforces $\le 1$ selection per match fixture in accumulator coupons.<br>Classes: Distinct events (valid) vs duplicate events (rejected). | Invariant: for every coupon $C$, $|\{s.\text{event\_id} : s \in C\}| == \text{len}(C)$. | Filters duplicate candidate legs, retaining the selection with highest objective value. | Tier 1 (5), Tier 2 (5), Tier 3, Tier 4 |
| **24** | Optimizer | Explicit Net EV & +EV filter | `PLAN_PROJEKTU.md` §4, `ORIGINAL_REQUEST.md` R4 | Valid: Displays exact Net EV ($p_{\text{true}} \cdot O_{\text{net}} \cdot k_{\text{pit}} - 1$). Toggle `only_plus_ev` restricts pool to $EV_{\text{net}} > 0$.<br>Boundary: $\text{EV} = 0.0000$. | If `only_plus_ev=True`, all returned coupons must satisfy `slip_ev_net > 0.0`.<br>Tolerance: $\pm 10^{-4}$. | If `only_plus_ev=True` and no $+EV$ bets exist, returns empty list with explanation. | Tier 1 (5), Tier 2 (5), Tier 3, Tier 4 |
| **25** | UI / UX | 1-Click Polish bookmaker override | `PLAN_PROJEKTU.md` §2.1, §4, `ORIGINAL_REQUEST.md` R4 | Valid: User overrides odds in coupon leg with exact STS/Fortuna/Betclic line via `POST /api/v1/slips/evaluate`.<br>Boundary: $O = 1.01$, large odds $100.0$.<br>Invalid: $O \le 1.00$. | Recomputes gross odds, net payout, and EV in $<50$ms.<br>$O_{\text{gross, new}} = \prod O_{\text{effective}, i}$. | UI shows red border on input $\le 1.00$; API returns HTTP 422 with validation error. | Tier 1 (5), Tier 2 (5), Tier 3, Tier 4 |
| **26** | UI / UX | 60-30-10 Design system | `design/STYL_I_GRAFIKI.md`, `PLAN_PROJEKTU.md` §6 | Valid: 60% Canvas Obsidian (`#0B0F19`), 30% Surface Slate (`#131C2E`), 10% Signal Emerald (`#10B981`) / Alpha Amber (`#F59E0B`).<br>Tabular numbers: `tabular-nums` on all odds/currency. | WCAG 2.2 AA contrast $\ge 4.5:1$ on body text, $\ge 3:1$ on large text and UI components. | Style lint failure on unauthorized neon colors, missing tabular-nums, or contrast violations. | Tier 1 (5), Tier 2 (5), Tier 3, Tier 4 |
| **27** | UI / UX | Rule "Never Color Alone" | `design/STYL_I_GRAFIKI.md` §2, `ORIGINAL_REQUEST.md` R5 | Valid: Color is never the sole semantic indicator.<br>Positive EV: `#10B981` + `+` + `▲` + `EV`.<br>Negative EV: `#F87171` + `-` + `▼` + `EV`.<br>Volatility: `#F59E0B` + warning icon + text. | Every rendered EV badge contains explicit textual sign (`+/-`) and directional glyph (`▲/▼`). | Accessibility assertion fails if EV badge renders color without text symbol / arrow. | Tier 1 (5), Tier 2 (5), Tier 3, Tier 4 |
| **28** | Auth & Legal | Auth & Legal 18+ / RODO gate | `PLAN_PROJEKTU.md` §8, §5.2, `ORIGINAL_REQUEST.md` R5 | Valid: Google OAuth / Email login with mandatory 18+ age verification and GDPR/RODO consent timestamps.<br>Classes: Compliant adult vs non-compliant/underage. | `users.accepted_terms_18_plus_at NOT NULL`.<br>`users.accepted_rodo_at NOT NULL`.<br>Account deletion cascade purges all user data. | Submit button disabled if 18+ unchecked; backend rejects registration with HTTP 400. | Tier 1 (5), Tier 2 (5), Tier 3, Tier 4 |
| **29** | Hosting | Cloudflare Pages + Render setup | `PLAN_PROJEKTU.md` §5.1, `ORIGINAL_REQUEST.md` R1, R5 | Valid: Static/SSR frontend on Cloudflare Pages reading Neon DB in <200ms; API on Render Free (~1 min cold start).<br>Classes: Warm API vs Cold API (loading skeleton). | SSR match lists never block on Render cold start.<br>Client timeout configured to 90 seconds. | UI displays animated terminal skeleton during cold start without crashing or premature timeout. | Tier 1 (5), Tier 2 (5), Tier 3, Tier 4 |

---

## 3. Test Architecture & Runner Harness

### 3.1 Directory Layout

```text
bukmacherka/
├── TEST_INFRA.md                     # Single source of truth test infrastructure specification (this document)
├── tests/
│   ├── fixtures/                     # 12 deterministic offline JSON fixture files
│   │   ├── sports_categories.json    # Active v1 sports + disabled Phase 2 sports (6 records)
│   │   ├── leagues.json              # Competition metadata and tier weights (10 records)
│   │   ├── competitor_ratings.json   # Strength metrics, xG, pace, Elo, Glicko-2 volatility (14 records)
│   │   ├── events.json               # Pre-match fixture schedule across sports (7 records)
│   │   ├── odds_snapshots.json       # Pinnacle sharp benchmark + Polish bookmaker odds (35 records)
│   │   ├── model_predictions.json    # Pre-calculated probabilities, fair odds, and EVs (12 records)
│   │   ├── users.json                # User profiles with 18+ and RODO compliance states (3 records)
│   │   ├── saved_slips.json          # Persisted user coupons across scenarios (4 records)
│   │   ├── devig_cases.json          # Benchmark 2-way, 3-way, and extreme favorite/longshot odds (8 records)
│   │   ├── tax_cases.json            # 0.88x, Betclic promo, Fortuna promo, 2280 PLN border (8 records)
│   │   ├── calibration_samples.json  # 120 historical betting events for Brier, Log-Loss, and CLV
│   │   └── design_tokens.json        # 60-30-10 palette hex codes, WCAG thresholds, Never Color Alone regexes
│   ├── helpers/
│   │   ├── __init__.py               # Package export for reusable assertion functions
│   │   └── assertions.py             # Reusable mathematical invariant assertion library
│   ├── conftest.py                   # Root pytest configuration, network guard, SQLite DB, mock repository
│   ├── run_e2e_tests.py              # Unified CLI test runner script
│   ├── test_harness_self_check.py    # Self-verifying sanity test suite for all harness components
│   └── e2e/
│       ├── tier1_features/           # Tier 1: Isolated feature coverage (>=145 tests, >=5 per feature)
│       ├── tier2_boundaries/         # Tier 2: Boundary & corner cases (>=145 tests, >=5 per feature)
│       ├── tier3_combinations/       # Tier 3: Cross-feature pairwise interactions (>=29 tests)
│       └── tier4_scenarios/          # Tier 4: Real-world user application workloads (>=15 scenarios)
```

### 3.2 Environment Variables & Execution Context

| Variable | Required Test Value | Description |
|---|---|---|
| `OFFLINE_MODE` | `true` | Enforces zero external HTTP/socket requests; activates deterministic local fixtures. |
| `ENABLE_PHASE2_SPORTS` | `false` (default) | Hides Volleyball and Table Tennis in v1 default views; toggled to `true` via fixture in Phase 2 tests. |
| `DATABASE_URL` | `sqlite:///:memory:` | In-memory SQLite emulation of Neon PostgreSQL with foreign keys enabled. |
| `APP_ENV` | `test` | Sets application runtime mode to test environment. |
| `PYTHONHASHSEED` | `42` | Guarantees deterministic Python dictionary hashing and iteration order. |
| `JWT_SECRET` | `test-secret-deterministic-key-quantkupon-32chars!` | Fixed HMAC secret for deterministic Auth.js token generation. |

### 3.3 Strict Network Isolation Guard

To enforce deterministic offline execution and prevent flaky network calls or accidental live API quota consumption, `tests/conftest.py` installs a session-scoped autouse socket interceptor:

```python
@pytest.fixture(scope="session", autouse=True)
def guard_offline_network() -> Generator[None, None, None]:
    orig_connect = socket.socket.connect

    def guarded_connect(self: socket.socket, address: Any) -> Any:
        host = address[0] if isinstance(address, tuple) else address
        # Allow local IPC / loopback for in-process testing
        if host in ("127.0.0.1", "localhost", "::1", None):
            return orig_connect(self, address)
        raise RuntimeError(
            f"External network connection blocked by QUANTKUPON offline test harness: {host}"
        )

    socket.socket.connect = guarded_connect
    yield
    socket.socket.connect = orig_connect
```

### 3.4 In-Memory SQLite Emulation of Neon PostgreSQL

Tests execute against an in-memory SQLite 3 database (`PRAGMA foreign_keys = ON;`) implementing all 9 Neon PostgreSQL tables:
- `sports_categories` (id, slug, name_pl, is_enabled_v1, volatility_tier, active_model)
- `leagues` (id, sport_id, name, country, tier_weight)
- `competitor_ratings` (competitor_id, sport_id, competitor_name, rating_elo, glicko_sigma, xg_attack, pace, ortg, etc.)
- `events` (id, league_id, home_competitor_id, away_competitor_id, home_team_name, away_team_name, start_time_utc, status, surface_or_format)
- `odds_snapshots` (id, event_id, bookmaker_key, market_key, outcome_key, odds_decimal, is_sharp_benchmark)
- `model_predictions` (id, event_id, market_key, outcome_key, p_model, p_sharp_devigged, p_true, fair_odds, estimated_pl_odds, ev_standard_pl, ev_taxfree_pl, kelly_quarter, factual_factors_json)
- `users` (id, name, email, accepted_terms_18_plus_at, accepted_rodo_at)
- `accounts` (id, user_id, provider, provider_account_id, access_token)
- `sessions` (id, session_token, user_id, expires)
- `saved_slips` (id, user_id, name, selections_json, custom_pl_odds_overrides_json, bookmaker_key, tax_multiplier, total_odds_gross, total_odds_net, potential_payout_net, joint_probability, slip_ev_net, recommended_kelly_stake_pct)

### 3.5 Unified CLI Runner (`tests/run_e2e_tests.py`)

The runner acts as a zero-dependency bootstrap script orchestrating virtual environments, injecting package paths into `PYTHONPATH`, and executing pytest with structured JUnit XML parsing:

```bash
python3 tests/run_e2e_tests.py [--tier {0,1,2,3,4,harness,all}] [--feature N] [--verbose] [--fail-fast] [--offline] [--ui] [--enforce-all] [--allow-empty] [--json]
```

#### CLI Flag Matrix

| Flag | Short | Default | Description |
|---|---|---|---|
| `--tier` | `-t` | `all` | Selects which tier to run: `0`/`harness` (sanity check), `1` (`tier1_features`), `2` (`tier2_boundaries`), `3` (`tier3_combinations`), `4` (`tier4_scenarios`), or `all`. |
| `--feature` | `-f` | `None` (all) | Filters tests for a specific feature number $N \in [1, 29]$ using `-k "feat_{N:02d} or feature_{N}"`. |
| `--verbose` | `-v` | `False` | Enables verbose test output, streaming test names and detailed failure tracebacks. |
| `--fail-fast` | `-x` | `False` | Halts execution immediately upon the first encountered test failure. |
| `--offline` | | `True` | Enforces `OFFLINE_MODE=true` deterministic execution. |
| `--ui` | | `False` | Includes Vitest frontend component tests (`apps/web`) in the run. |
| `--enforce-all` | | `False` | Strict mode (Milestone E2E-M6 gate): requires all 4 tiers to exist and meet minimum test thresholds. |
| `--allow-empty` | | `False` | Allows exit code 0 even if 0 tests are discovered (used for early scaffolding dry-runs). |
| `--json` | | `False` | Outputs machine-readable JSON summary of results to stdout. |

#### Exit Code Contract

| Exit Code | Condition | Meaning |
|---|---|---|
| `0` | Discovered tests > 0, failed == 0, errors == 0 | **100% Pass:** Build/test gate passes. All discovered tests executed successfully. |
| `1` | Discovered tests > 0, (failed + errors) > 0 | **Test Failure:** Inspect failure diagnostics block, fix code or fixture logic. |
| `2` | `argparse` validation error | **CLI Usage Error:** Check command arguments (`--tier`, `--feature`). |
| `3` | Total discovered tests == 0 (without `--allow-empty`) | **Empty Suite Guard:** Prevents false-positive CI pass on missing test files. |
| `4` | `pytest` runtime missing in `.venv` and system PATH | **Environment Error:** Initialize `.venv` and install pytest. |

---

## 4. Real-World Application Workload Scenarios (Tier 4: 16 Scenarios)

The Tier 4 test suite verifies complete end-to-end user journeys and cross-system workflows:

1. **Scenario 1: Football 3-leg Accumulator (Premier League / La Liga) with Betclic Zero-Tax Promotion**  
   - *Flow:* User requests a 3-leg football coupon with target odds 3.0–4.0 in Betclic mode. Selections: Arsenal ML (1.45), Real Madrid ML (1.35), Barcelona vs Valencia Over 2.5 (1.60).
   - *Verification:* Combined gross odds $= 1.45 \times 1.35 \times 1.60 = 3.132$. Every leg has $O_i \ge 1.20$ and legs $\ge 2 \implies k_{\text{tax}} = 1.00$. Net odds $= 3.132$. Payout on 100 PLN stake $= 313.20$ PLN. PIT applies $= \text{False}$. Net EV correctly matches joint probability $\times 3.132 - 1$.

2. **Scenario 2: High-Payout Accumulator Triggering 10% PIT Threshold (> 2280 PLN) & Split Advice**  
   - *Flow:* User selects 4 high-value legs with combined gross odds of $28.50$ and stakes $100.00$ PLN in standard 0.88x tax mode.
   - *Verification:* Net odds $= 28.50 \times 0.88 = 25.08$. Tentative gross payout $= 2508.00$ PLN. Because $2508.00 > 2280.00$, engine flags `pit_10_applies = True`, deducts 10% PIT ($250.80$ PLN), yielding net payout $2257.20$ PLN. Engine generates `SplitAdvice`: recommend splitting into 2 tickets of stake $50.00$ PLN each (payout $1254.00$ PLN $\le 2280.00$), saving exactly $250.80$ PLN in tax!

3. **Scenario 3: 1-Click Polish Bookmaker Odds Override on Basketball NBA Spread with Instant Recalculation**  
   - *Flow:* User generates a 2-leg coupon featuring Boston Celtics -5.5 (default odds 1.82) and LA Lakers ML (1.75). User checks their STS mobile app and types `1.90` into the Celtics override field.
   - *Verification:* Client sends `POST /api/v1/slips/evaluate` with override `{ event_id: 'ev_bb_bos_nyk', odds_override: 1.90 }`. Engine recomputes gross odds from $3.185$ to $3.325$, net odds (0.88x) to $2.926$, updates Net EV live, and verifies quarter-Kelly stake fraction updates accordingly within 50ms.

4. **Scenario 4: Tennis Tournament Best-of-3 Clay Match Analysis with Surface Elo & Markov Chain**  
   - *Flow:* User views `/analiza/tenis-ziemny` for Roland Garros match between Player A (Clay Elo 2100, serve win 68%) and Player B (Clay Elo 1950, serve win 62%).
   - *Verification:* Tennis model calculates game winning probabilities via absorbing deuce formula, computes tiebreak dynamic programming matrix, and aggregates Bo3 tree. Validates $P(\text{Player A}) + P(\text{Player B}) = 1.0 \pm 10^{-5}$, $P(2:0) + P(2:1) + P(1:2) + P(0:2) = 1.0 \pm 10^{-5}$, and set handicap lines align with game total distributions.

5. **Scenario 5: Ice Hockey NHL Regulation Draw with Empty Net Late-Game Correction**  
   - *Flow:* Ingests NHL game Edmonton Oilers vs Calgary Flames ($\lambda = 3.2, \mu = 2.8$).
   - *Verification:* Regulation 60' Skellam distribution computes $P(1), P(X), P(2)$ summing to $1.0 \pm 10^{-5}$. Empty net correction triggers for trailing team by 1-2 goals, inflating goal arrival rates by $\kappa_{\text{EN}} = 3.2\times$. Over 5.5 goal probability increases from $54.2\%$ to $61.8\%$ and Puck Line -1.5 adjusts accurately.

6. **Scenario 6: Table Tennis Volatility Guard Triggering Dynamic Shrinkage & Amber Alert**  
   - *Flow:* Environment flag `ENABLE_PHASE2_SPORTS=true`. Fixture from Setka Cup involves player with only 2 recorded matches in DB ($\sigma = 0.088 > 0.06$, $RD = 260$).
   - *Verification:* Volatility Guard activates; collapses model weight from $0.30$ to $0.10$, blending $90\%$ with sharp market consensus. Response payload sets `is_high_volatility = True`, and UI displays Amber `#F59E0B` alert badge with text "Podwyższona wariancja (Glicko-2 σ)".

7. **Scenario 7: Mixed Multi-Sport Accumulator with Anti-Correlation Guard Enforcement**  
   - *Flow:* User requests coupon covering Football, Basketball, Tennis, and Hockey. Candidate pool contains 2 selections from Arsenal vs Chelsea (Arsenal Win and Over 2.5 Goals).
   - *Verification:* Anti-Correlation Guard detects identical `event_id`, filters out the Over 2.5 selection, and retains only Arsenal Win. Generated 4-leg coupon contains exactly 1 leg per match across 4 different sports, satisfying all individual and joint probability invariants.

8. **Scenario 8: User Registration with Strict 18+ Age Verification & RODO Consent, Saving Coupon to `/moje-kupony`**  
   - *Flow:* New user signs up via Google OAuth with 18+ and RODO checkboxes checked. Generates coupon and clicks "Zapisz kupon".
   - *Verification:* User record created in Neon PostgreSQL with non-null `accepted_terms_18_plus_at` and `accepted_rodo_at`. Coupon is saved to `saved_slips` linked to `user_id`. Querying `GET /api/v1/slips/saved` returns the slip with all selections and recalculation metadata intact.

9. **Scenario 9: User Invoking GDPR "Right to be Forgotten" Account Erasure with Atomic Purge**  
   - *Flow:* Authenticated user with 5 saved slips navigates to profile and clicks "Usuń konto i wszystkie dane".
   - *Verification:* User account deleted via `DELETE /api/v1/users/me`. PostgreSQL foreign keys with `ON DELETE CASCADE` execute atomically; confirms 0 records remaining in `users`, `accounts`, `sessions`, and `saved_slips` for that user ID.

10. **Scenario 10: Render Free Cold-Start Simulation during Coupon Generation with Graceful Recovery**  
    - *Flow:* Client requests `POST /api/v1/slips/generate` after simulated 30-minute idle sleep (delay 45 seconds).
    - *Verification:* Frontend UI transitions to loading terminal skeleton with message "Inicjalizacja silnika matematycznego...", does not freeze or time out prematurely, and gracefully renders optimized coupons when API completes at $t = 45$s.

11. **Scenario 11: Infeasible Target Odds Range in Coupon Generator Returning Graceful Empty State**  
    - *Flow:* User requests coupon with odds range $[1.50, 1.60]$ requiring $\ge 3$ legs, but minimum single odds in candidate pool is $1.35$ ($1.35^3 = 2.46 > 1.60$).
    - *Verification:* Solver detects impossibility; returns HTTP 200 with `{"coupons": []}` and feedback message: "Brak kuponów spełniających zadane kryteria. Rozważ zmniejszenie liczby nóg lub zwiększenie maksymalnego kursu całkowitego".

12. **Scenario 12: Offline Deterministic Batch Ingestion Pipeline Executing 2x Daily Cron Simulation**  
    - *Flow:* Test runner executes cron workflow in offline mode (`OFFLINE_MODE=true`) using mock data from `tests/fixtures/`.
    - *Verification:* Mock feeds parse football, basketball, tennis, and hockey pre-match fixtures; quant-engine models compute predictions; PolishTaxEngine assigns tax multipliers; records upsert into mock Neon DB state with zero external HTTP requests made.

13. **Scenario 13: Quantitative Calibration & Audit Pipeline with Brier Score, Log-Loss, and CLV**  
    - *Flow:* Historical evaluation dataset of 500 completed matches loaded.
    - *Verification:* Engine calculates Brier Score ($0.182$), Log-Loss ($0.541$), and CLV ($+3.2\%$). Validates all metrics fall within theoretical bounds ($0 \le \text{BS} \le 1$, $\text{LL} \ge 0$) and reliability diagram deciles align monotonically with empirical frequencies.

14. **Scenario 14: Fractional Quarter-Kelly Staking under High Positive EV with 5% Safety Cap**  
    - *Flow:* Edge case match where bookmaker offers odds $2.80$ while true model probability is $0.60$ (Net EV with 0.88x tax $= 0.60 \times (2.80 \times 0.88) - 1 = +47.8\%$).
    - *Verification:* Raw Quarter-Kelly formula yields $0.25 \times \frac{0.60 \times 1.464 - 0.40}{1.464} = 0.0817$ (8.17%). Fractional Kelly engine enforces strict ceiling: recommended stake fraction $f^* = 0.0500$ (5.0% exactly).

15. **Scenario 15: De-vigging Solver Stress Test Across Extreme Odds Distributions**  
    - *Flow:* Tests Shin, Power, and Multiplicative methods across 100 random market odds vectors including extreme favorites ($1.02, 35.0$), balanced 3-way markets ($2.50, 3.20, 2.90$), and high overround lines ($M = 0.15$).
    - *Verification:* All solvers maintain $\sum p_i = 1.0 \pm 10^{-6}$. Shin insider parameter $z \in [0, 1)$ converges in $<15$ iterations for normal overrounds. Shin fair probabilities strictly penalize longshots more than Multiplicative method (eliminating favorite-longshot bias).

16. **Scenario 16: Never Color Alone WCAG 2.2 AA Accessibility Compliance Across All Value Indicators**  
    - *Flow:* Automated DOM inspector evaluates all rendered EV badges, odds movements, and volatility warnings on `/analiza/[sport]` and `/generator-kuponow`.
    - *Verification:* Confirms zero instances of color-only semantic encoding: all positive EV indicators contain `#10B981` + `+` + `▲` + `EV`; all negative EV indicators contain `#F87171` + `-` + `▼` + `EV`; all Table Tennis volatility alerts contain `#F59E0B` + warning icon + text "Podwyższona wariancja σ". Contrast ratios exceed $4.5:1$ across all text nodes.

---

## 5. Mathematical Invariants, Tolerances, and Helper Assertions

The reusable mathematical assertion library is implemented in `tests/helpers/assertions.py` and exported across all test modules:

1. **Probability Distribution Normalization:**  
   $$\sum_{i=1}^k p_i = 1.0 \pm 10^{-5}, \quad p_i \in [0.0, 1.0] \quad \forall i$$
   `assert_probability_distribution(probabilities, tolerance=1e-5)`

2. **De-vigging Convergence & Monotonicity:**  
   - Solvers converge within tolerance $\epsilon \le 10^{-6}$.
   - Monotonicity preservation: if $O_a < O_b \implies p_a \ge p_b - \epsilon$.
   `assert_devig_convergence(devigged_probs, original_odds, method="shin", tolerance=1e-5)`

3. **Polish Turnover Tax (Ustawa o grach hazardowych):**  
   - Statutory: $O_{\text{net}} = 0.88 \cdot O_{\text{gross}}$, $W_{\text{net}} = S \cdot O_{\text{net}}$.
   - Promotional: $O_{\text{net}} = 1.00 \cdot O_{\text{gross}}$, $W_{\text{net}} = S \cdot O_{\text{net}}$.
   `assert_polish_turnover_tax(stake, gross_odds, calculated_net_odds, calculated_net_payout, is_promotional=False, tolerance=0.02)`

4. **10% PIT Deduction Threshold (2280.00 PLN):**  
   - If gross payout $W \le 2280.00$ PLN: `pit_10_applies = False`, `pit_deduction = 0.00`, $W_{\text{net}} = W$.
   - If gross payout $W > 2280.00$ PLN: `pit_10_applies = True`, `pit_deduction = round(0.10 * W, 2)`, $W_{\text{net}} = \text{round}(0.90 * W, 2)$.
   `assert_polish_pit_threshold(gross_payout, calculated_net_payout, pit_applies, pit_deduction, tolerance=0.02)`

5. **Ticket Splitting Advice:**  
   - If $2280.00 < W \le 4560.00$ PLN: suggests 2 tickets of stake $S/2$, saving $0.10 \cdot W$.
   `assert_ticket_splitting_advice(stake, gross_payout, split_advice)`

6. **Anti-Correlation Guard:**  
   - Accumulator coupons cannot contain duplicate match selections:
     $$|\{s.\text{event\_id} : s \in C\}| == \text{len}(C)$$
   `assert_anti_correlation_guard(selections)`

7. **Fractional Quarter-Kelly Staking:**  
   - $f^* = 0.0$ if $\text{EV} \le 0$; $0.0 \le f^* \le 0.05$ (5% max cap).
   `assert_fractional_kelly(fraction, expected_value, max_cap=0.05)`

8. **"Never Color Alone" Accessibility Rule:**  
   - Positive EV indicator requires `+` and `▲` or `↑`.
   - Negative EV indicator requires `-` and `▼` or `↓`.
   `assert_never_color_alone(badge_label, ev_value)`

9. **WCAG 2.2 AA Contrast Compliance:**  
   - Contrast ratio $(L_1 + 0.05) / (L_2 + 0.05) \ge 4.5$ for body text.
   `assert_wcag_contrast(foreground_hex, background_hex, min_ratio=4.5)`

---

## 6. Coverage Thresholds & Progressive Verification Gates

To guarantee enterprise-grade mathematical rigor and product quality, the test suite enforces the following hierarchical thresholds:

| Tier | Directory | Primary Scope | Minimum Passing Tests |
|---|---|---|---|
| **Harness** | `tests/test_harness_self_check.py` | Sanity check for network isolation, fixtures, SQLite DDL, and assertion helpers | $\ge 21$ tests |
| **Tier 1** | `tests/e2e/tier1_features/` | Feature coverage across all 29 features ($\ge 5$ tests per feature) | $\ge 145$ tests |
| **Tier 2** | `tests/e2e/tier2_boundaries/` | Boundary, corner cases, tolerances, 2280 PLN borders, zero/negative inputs ($\ge 5$ tests per feature) | $\ge 145$ tests |
| **Tier 3** | `tests/e2e/tier3_combinations/` | Pairwise cross-feature interactions and integration pipelines | $\ge 29$ tests |
| **Tier 4** | `tests/e2e/tier4_scenarios/` | Real-world application workloads (all 16 scenarios) | $\ge 15$ tests |
| **Total** | `tests/` | **Full Monorepo E2E Test Suite** | **$\ge 355$ tests** |

### Execution Commands

```bash
# Run all discovered tests in offline deterministic mode
python3 tests/run_e2e_tests.py

# Run with streaming verbose logs
python3 tests/run_e2e_tests.py --verbose

# Run a specific tier (e.g. Tier 1)
python3 tests/run_e2e_tests.py --tier 1

# Filter for a specific feature (e.g. Feature 16: PIT 10% threshold)
python3 tests/run_e2e_tests.py --feature 16

# Run harness sanity self-check
python3 tests/run_e2e_tests.py --tier harness

# Strict full verification enforcement (Milestone E2E-M6 gate)
python3 tests/run_e2e_tests.py --tier all --enforce-all
```

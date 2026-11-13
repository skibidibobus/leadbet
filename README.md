# LeadBet

Narzędzie analityczne **pre-match** do porównywania prawdopodobieństw modeli sportowych z rynkiem referencyjnym (de-vigging Shina), optymalizacji kuponów z blokadą korelacji oraz kalkulacji polskich podatków bukmacherskich (12% podatek obrotowy `0.88×`, promocje `1.00×` oraz 10% PIT powyżej `2280.00 PLN`).

**Podgląd online (GitHub Pages):** https://skibidibobus.github.io/leadbet/

---

## Zakres i architektura

- **`apps/web`** — Frontend Next.js 15 (App Router, React 19, Tailwind CSS), w trybie statycznym działa w pełni offline na wbudowanym zestawie danych lub łączy się z API przez `NEXT_PUBLIC_API_URL`.
- **`apps/api`** — Backend FastAPI (`/api/v1/categories`, `/events`, `/events/{id}/breakdown`, `/slips/generate`, `/slips/evaluate`, `/slips/saved`, `/calibration/metrics`) oraz skrypt cykliczny `cron_ingest.py` (2×/dzień pre-match).
- **`packages/quant-engine`** — Modele probabilistyczne (Dixon-Coles, Pace ORtg/DRtg, Surface Markov Elo, Skellam 60m), de-vigging Shina/Power, fuzja bayesowska, ułamkowy Kelly (`0.25×`, limit `5%`) i optymalizator wiązkowy z Anti-Correlation Guard.
- **`packages/bookmaker-adapters`** — Polski silnik podatkowy (`PolishTaxEngine` z progami `2280.00 PLN` i `SplitAdvice`) oraz adaptery źródeł pre-match (`SnapshotFixtureAdapter`, `TheOddsApiAdapter`).

---

## Uruchomienie lokalne

### 1. Backend (FastAPI, port `8000`)

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -e packages/quant-engine -e packages/bookmaker-adapters
pip install fastapi uvicorn httpx pytest pydantic

PYTHONPATH=apps/api:packages/quant-engine:packages/bookmaker-adapters \
  uvicorn src.main:app --reload --port 8000
```

### 2. Frontend (Next.js, port `3000`)

```bash
cd apps/web
npm install
npm run dev
```

### 3. Testy

```bash
PYTHONPATH=apps/api:packages/quant-engine:packages/bookmaker-adapters pytest packages/ apps/api/ -v
cd apps/web && npm run type-check && npm run build
```

---

## Bezpieczeństwo i zgodność z prawem w Polsce

- **Charakter wyłącznie analityczny:** LeadBet nie przyjmuje zakładów wzajemnych, nie obsługuje płatności ani depozytów i nie publikuje zachęt do gry ani linków afiliacyjnych.
- **Brak promocji nielicencjonowanych podmiotów:** Zewnętrzne kursy referencyjne służą wyłącznie do estymacji matematycznego prawdopodobieństwa (`p_sharp`), natomiast symulacje podatku obrotowego (`0.88×` / `1.00×`) i PIT (`10% > 2280 PLN`) odnoszą się do polskich przepisów podatkowych.
- **Przeznaczenie 18+ i RODO:** Interfejs zawiera jawne oznaczenie `18+` oraz informację o ryzyku związanym z zakładami bukmacherskimi.
- **Brak sekretów w repozytorium:** Wszystkie klucze (`THE_ODDS_API_KEY`, `DATABASE_URL`) przekazywane są wyłącznie przez zmienne środowiskowe (`.env.example`).

---

## Licencja

[MIT](LICENSE)

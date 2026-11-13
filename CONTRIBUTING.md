# Contributing to LeadBet

1. Fork the repository and create a branch from `main`.
2. Keep changes focused and verify both backend and frontend checks before opening a pull request:
   - Backend tests: `PYTHONPATH=apps/api:packages/quant-engine:packages/bookmaker-adapters pytest packages/ apps/api/ -v`
   - Frontend type-check & build: `cd apps/web && npm run type-check && npm run build`
3. Do not commit `.env` files, API keys, or build artifacts (`.next/`, `out/`, `.venv/`).
4. Ensure all user-facing copy remains strictly analytical/informational and compliant with Polish law (18+, no betting recommendations or unlicensed operator promotion).

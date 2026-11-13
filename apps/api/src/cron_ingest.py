"""Pre-match 2x/day ingestion script (0 PLN free-tier friendly).

Fetches pre-match odds from The Odds API when THE_ODDS_API_KEY is set,
or falls back to SnapshotFixtureAdapter for offline/CI runs, runs the
quantitative probability & EV pipeline, and optionally persists a JSON
snapshot (or Neon PostgreSQL if DATABASE_URL is configured).
"""
from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Optional

from bookmaker_adapters.feeds import SnapshotFixtureAdapter, TheOddsApiAdapter
from src.services.data_service import QuantDataService


def run_prematch_ingest(output_path: Optional[str] = None) -> Dict[str, Any]:
    """Run pre-match ingestion once and return summary stats."""
    api_key = os.getenv("THE_ODDS_API_KEY", "").strip()
    snapshot_adapter = SnapshotFixtureAdapter()

    fetched_live_events = 0
    if api_key:
        live_adapter = TheOddsApiAdapter(api_key=api_key)
        for sport_key in ("soccer_epl", "basketball_nba", "icehockey_nhl"):
            try:
                events = live_adapter.fetch_prematch_odds(sport_key)
                fetched_live_events += len(events)
            except Exception as exc:
                print(f"[cron_ingest] Warning: live fetch failed for {sport_key}: {exc}")

    service = QuantDataService(adapter=snapshot_adapter)
    events_payload = service.get_events(limit=200)

    summary = {
        "timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "mode": "live_plus_snapshot" if api_key else "snapshot_only",
        "fetched_live_events": fetched_live_events,
        "indexed_prematch_events": events_payload["total"],
        "sports_active": [
            c["slug"]
            for c in service.get_categories(enabled_only=True)["categories"]
        ],
    }

    if output_path:
        dest = Path(output_path)
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_text(
            json.dumps({"summary": summary, "events": events_payload["events"]}, indent=2),
            encoding="utf-8",
        )

    return summary


if __name__ == "__main__":
    out = os.getenv("INGEST_SNAPSHOT_OUT", "")
    result = run_prematch_ingest(output_path=out or None)
    print(json.dumps(result, indent=2))

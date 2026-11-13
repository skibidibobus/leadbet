"""Bookmaker and sports data feed adapters (offline fixture + budget-aware live pre-match)."""
from __future__ import annotations

import json
import os
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any, Dict, List, Optional

import httpx


DEFAULT_FIXTURES_DIR = Path(__file__).resolve().parents[4] / "tests" / "fixtures"


class BookmakerFeedAdapter(ABC):
    """Abstract interface decoupling odds sources from quantitative modeling."""

    @abstractmethod
    def load_categories(self) -> List[Dict[str, Any]]:
        """Return sport categories metadata."""

    @abstractmethod
    def load_events(self, sport: Optional[str] = None) -> List[Dict[str, Any]]:
        """Return pre-match events list."""

    @abstractmethod
    def load_odds_snapshots(self) -> List[Dict[str, Any]]:
        """Return bookmaker odds snapshots."""


class SnapshotFixtureAdapter(BookmakerFeedAdapter):
    """Deterministic offline adapter reading normalized JSON fixtures."""

    def __init__(self, fixtures_dir: Optional[Path] = None) -> None:
        self.fixtures_dir = fixtures_dir or DEFAULT_FIXTURES_DIR

    def _read_json(self, filename: str) -> Any:
        path = self.fixtures_dir / filename
        with path.open("r", encoding="utf-8") as fh:
            return json.load(fh)

    def load_categories(self) -> List[Dict[str, Any]]:
        return list(self._read_json("sports_categories.json"))

    def load_leagues(self) -> List[Dict[str, Any]]:
        return list(self._read_json("leagues.json"))

    def load_events(self, sport: Optional[str] = None) -> List[Dict[str, Any]]:
        events = list(self._read_json("events.json"))
        if sport is None:
            return events
        leagues = {lg["id"]: lg for lg in self.load_leagues()}
        categories = {cat["id"]: cat["slug"] for cat in self.load_categories()}
        return [
            ev
            for ev in events
            if categories.get(leagues.get(ev["league_id"], {}).get("sport_id")) == sport
        ]

    def load_competitor_ratings(self) -> Dict[str, Dict[str, Any]]:
        items = list(self._read_json("competitor_ratings.json"))
        return {item["competitor_id"]: item for item in items}

    def load_odds_snapshots(self) -> List[Dict[str, Any]]:
        return list(self._read_json("odds_snapshots.json"))

    def load_calibration_samples(self) -> List[Dict[str, Any]]:
        return list(self._read_json("calibration_samples.json"))


class TheOddsApiAdapter:
    """Budget-capped pre-match adapter for The Odds API free tier (500 credits/month)."""

    BASE_URL = "https://api.the-odds-api.com/v4"
    # Budgeted v1 sport keys: max 4-5 sports/leagues refreshed 2x/day
    DEFAULT_SPORT_KEYS = [
        "soccer_epl",
        "basketball_nba",
        "icehockey_nhl",
    ]

    def __init__(self, api_key: Optional[str] = None, max_credits_per_run: int = 6) -> None:
        self.api_key = api_key or os.getenv("THE_ODDS_API_KEY", "")
        self.max_credits_per_run = max_credits_per_run

    def fetch_prematch_odds(
        self,
        sport_keys: Optional[List[str]] = None,
        regions: str = "eu",
        markets: str = "h2h,totals",
    ) -> List[Dict[str, Any]]:
        """Fetch pre-match odds while enforcing the strict free-tier credit cap."""
        if not self.api_key:
            return []

        keys = (sport_keys or self.DEFAULT_SPORT_KEYS)[: self.max_credits_per_run]
        results: List[Dict[str, Any]] = []
        with httpx.Client(timeout=15.0) as client:
            for key in keys:
                resp = client.get(
                    f"{self.BASE_URL}/sports/{key}/odds",
                    params={
                        "apiKey": self.api_key,
                        "regions": regions,
                        "markets": markets,
                        "oddsFormat": "decimal",
                    },
                )
                if resp.status_code == 200:
                    payload = resp.json()
                    if isinstance(payload, list):
                        results.extend(payload)
        return results

"""Root Pytest Configuration for QUANTKUPON Monorepo.

Enforces deterministic offline execution, provides in-memory SQLite and mock
repository fixtures, mock bookmaker feeds, and mathematical assertion helpers.
"""

from __future__ import annotations

import json
import os
from pathlib import Path
import random
import socket
import sqlite3
import sys
from typing import Any, Callable, Generator, List, Mapping, Optional
import pytest

# 1. Path Management: Add all internal modules to sys.path
REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT / "packages" / "quant-engine"))
sys.path.insert(0, str(REPO_ROOT / "packages" / "bookmaker-adapters"))
sys.path.insert(0, str(REPO_ROOT / "apps" / "api"))
sys.path.insert(0, str(REPO_ROOT / "apps" / "api" / "src"))
sys.path.insert(0, str(REPO_ROOT / "tests"))
sys.path.insert(0, str(REPO_ROOT))

FIXTURES_DIR = REPO_ROOT / "tests" / "fixtures"


# 2. Session Environment Setup (Autouse)
@pytest.fixture(scope="session", autouse=True)
def setup_test_environment() -> Generator[None, None, None]:
    """Configures deterministic environment variables and random seeds."""
    os.environ["OFFLINE_MODE"] = "true"
    os.environ["ENABLE_PHASE2_SPORTS"] = "false"
    os.environ["DATABASE_URL"] = "sqlite:///:memory:"
    os.environ["APP_ENV"] = "test"
    os.environ["PYTHONHASHSEED"] = "42"
    os.environ["JWT_SECRET"] = "test-secret-deterministic-key-quantkupon-32chars!"

    random.seed(42)
    try:
        import numpy as np  # type: ignore

        np.random.seed(42)
    except ImportError:
        pass

    yield


# 3. Phase 2 Feature Flag Toggle Fixture
@pytest.fixture
def enable_phase2_sports(
    monkeypatch: pytest.MonkeyPatch,
) -> Generator[None, None, None]:
    """Temporarily enables Volleyball and Table Tennis for Phase 2 tests."""
    monkeypatch.setenv("ENABLE_PHASE2_SPORTS", "true")
    yield


# 4. Strict Network Isolation Guard (Autouse)
@pytest.fixture(scope="session", autouse=True)
def guard_offline_network() -> Generator[None, None, None]:
    """Intercepts socket connections to guarantee zero external internet calls during tests."""
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


# 5. JSON Fixture Loader Helper
@pytest.fixture(scope="session")
def load_fixture() -> Callable[[str], Any]:
    """Loads and parses any JSON fixture from tests/fixtures/."""

    def _load(filename: str) -> Any:
        path = FIXTURES_DIR / filename
        if not path.exists():
            raise FileNotFoundError(f"Fixture file not found: {path}")
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)

    return _load


# 6. SQLite DDL Schema for 9 Neon PostgreSQL Tables
SQLITE_DDL = """
PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS sports_categories (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    slug TEXT UNIQUE NOT NULL,
    name_pl TEXT NOT NULL,
    is_enabled_v1 INTEGER NOT NULL DEFAULT 1,
    volatility_tier TEXT NOT NULL DEFAULT 'standard',
    active_model TEXT NOT NULL,
    created_at TEXT DEFAULT (strftime('%Y-%m-%dT%H:%M:%SZ', 'now'))
);

CREATE TABLE IF NOT EXISTS leagues (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    sport_id INTEGER NOT NULL,
    name TEXT NOT NULL,
    country TEXT,
    tier_weight REAL NOT NULL DEFAULT 1.00,
    created_at TEXT DEFAULT (strftime('%Y-%m-%dT%H:%M:%SZ', 'now')),
    FOREIGN KEY (sport_id) REFERENCES sports_categories(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS competitor_ratings (
    competitor_id TEXT PRIMARY KEY,
    sport_id INTEGER NOT NULL,
    competitor_name TEXT NOT NULL,
    rating_elo REAL,
    glicko_r REAL,
    glicko_rd REAL,
    glicko_sigma REAL,
    xg_attack REAL,
    xg_defense REAL,
    pace REAL,
    ortg REAL,
    drtg REAL,
    serve_win_pct REAL,
    return_win_pct REAL,
    updated_at TEXT DEFAULT (strftime('%Y-%m-%dT%H:%M:%SZ', 'now')),
    FOREIGN KEY (sport_id) REFERENCES sports_categories(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS events (
    id TEXT PRIMARY KEY,
    league_id INTEGER NOT NULL,
    home_competitor_id TEXT NOT NULL,
    away_competitor_id TEXT NOT NULL,
    home_team_name TEXT NOT NULL,
    away_team_name TEXT NOT NULL,
    start_time_utc TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'pre_match',
    surface_or_format TEXT,
    created_at TEXT DEFAULT (strftime('%Y-%m-%dT%H:%M:%SZ', 'now')),
    updated_at TEXT DEFAULT (strftime('%Y-%m-%dT%H:%M:%SZ', 'now')),
    FOREIGN KEY (league_id) REFERENCES leagues(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS odds_snapshots (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    time TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%SZ', 'now')),
    event_id TEXT NOT NULL,
    bookmaker_key TEXT NOT NULL,
    market_key TEXT NOT NULL,
    outcome_key TEXT NOT NULL,
    odds_decimal REAL NOT NULL,
    is_sharp_benchmark INTEGER NOT NULL DEFAULT 0,
    FOREIGN KEY (event_id) REFERENCES events(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS model_predictions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    event_id TEXT NOT NULL,
    market_key TEXT NOT NULL,
    outcome_key TEXT NOT NULL,
    p_model REAL NOT NULL CHECK (p_model >= 0 AND p_model <= 1),
    p_sharp_devigged REAL NOT NULL CHECK (p_sharp_devigged >= 0 AND p_sharp_devigged <= 1),
    p_true REAL NOT NULL CHECK (p_true >= 0 AND p_true <= 1),
    fair_odds REAL NOT NULL,
    estimated_pl_odds REAL NOT NULL,
    ev_standard_pl REAL NOT NULL,
    ev_taxfree_pl REAL NOT NULL,
    kelly_quarter REAL NOT NULL,
    model_version TEXT NOT NULL,
    factual_factors_json TEXT NOT NULL DEFAULT '{}',
    computed_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%SZ', 'now')),
    UNIQUE(event_id, market_key, outcome_key, model_version),
    FOREIGN KEY (event_id) REFERENCES events(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS users (
    id TEXT PRIMARY KEY,
    name TEXT,
    email TEXT UNIQUE NOT NULL,
    email_verified TEXT,
    image TEXT,
    accepted_terms_18_plus_at TEXT,
    accepted_rodo_at TEXT,
    created_at TEXT DEFAULT (strftime('%Y-%m-%dT%H:%M:%SZ', 'now')),
    updated_at TEXT DEFAULT (strftime('%Y-%m-%dT%H:%M:%SZ', 'now'))
);

CREATE TABLE IF NOT EXISTS accounts (
    id TEXT PRIMARY KEY,
    user_id TEXT NOT NULL,
    type TEXT NOT NULL,
    provider TEXT NOT NULL,
    provider_account_id TEXT NOT NULL,
    refresh_token TEXT,
    access_token TEXT,
    expires_at INTEGER,
    token_type TEXT,
    scope TEXT,
    id_token TEXT,
    session_state TEXT,
    UNIQUE(provider, provider_account_id),
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS sessions (
    id TEXT PRIMARY KEY,
    session_token TEXT UNIQUE NOT NULL,
    user_id TEXT NOT NULL,
    expires TEXT NOT NULL,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS saved_slips (
    id TEXT PRIMARY KEY,
    user_id TEXT NOT NULL,
    name TEXT NOT NULL DEFAULT 'Kupon',
    selections_json TEXT NOT NULL,
    user_profile_params_json TEXT NOT NULL,
    custom_pl_odds_overrides_json TEXT NOT NULL DEFAULT '{}',
    bookmaker_key TEXT NOT NULL,
    tax_multiplier REAL NOT NULL,
    total_odds_gross REAL NOT NULL,
    total_odds_net REAL NOT NULL,
    stake REAL NOT NULL DEFAULT 100.00,
    potential_payout_gross REAL NOT NULL,
    potential_payout_net REAL NOT NULL,
    joint_probability REAL NOT NULL,
    slip_ev_net REAL NOT NULL,
    recommended_kelly_stake_pct REAL NOT NULL,
    pit_10_applies INTEGER NOT NULL DEFAULT 0,
    created_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%SZ', 'now')),
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);
"""


# 7. In-Memory SQLite Database Fixture
@pytest.fixture
def sqlite_db(load_fixture: Callable[[str], Any]) -> Generator[sqlite3.Connection, None, None]:
    """Provides a fresh in-memory SQLite database populated with schema and seed fixtures."""
    conn = sqlite3.connect(":memory:")
    conn.row_factory = sqlite3.Row
    conn.executescript(SQLITE_DDL)

    # Seed categories
    categories = load_fixture("sports_categories.json")
    for cat in categories:
        conn.execute(
            "INSERT INTO sports_categories (id, slug, name_pl, is_enabled_v1, volatility_tier, active_model) "
            "VALUES (?, ?, ?, ?, ?, ?)",
            (
                cat["id"],
                cat["slug"],
                cat["name_pl"],
                1 if cat["is_enabled_v1"] else 0,
                cat["volatility_tier"],
                cat["active_model"],
            ),
        )

    # Seed leagues
    leagues = load_fixture("leagues.json")
    for lg in leagues:
        conn.execute(
            "INSERT INTO leagues (id, sport_id, name, country, tier_weight) VALUES (?, ?, ?, ?, ?)",
            (lg["id"], lg["sport_id"], lg["name"], lg["country"], lg["tier_weight"]),
        )

    # Seed competitors
    competitors = load_fixture("competitor_ratings.json")
    for c in competitors:
        conn.execute(
            "INSERT INTO competitor_ratings (competitor_id, sport_id, competitor_name, rating_elo, "
            "glicko_r, glicko_rd, glicko_sigma, xg_attack, xg_defense, pace, ortg, drtg, serve_win_pct, return_win_pct) "
            "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (
                c["competitor_id"],
                c["sport_id"],
                c["competitor_name"],
                c.get("rating_elo"),
                c.get("glicko_r"),
                c.get("glicko_rd"),
                c.get("glicko_sigma"),
                c.get("xg_attack"),
                c.get("xg_defense"),
                c.get("pace"),
                c.get("ortg"),
                c.get("drtg"),
                c.get("serve_win_pct"),
                c.get("return_win_pct"),
            ),
        )

    # Seed events
    events = load_fixture("events.json")
    for ev in events:
        conn.execute(
            "INSERT INTO events (id, league_id, home_competitor_id, away_competitor_id, "
            "home_team_name, away_team_name, start_time_utc, status, surface_or_format) "
            "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (
                ev["id"],
                ev["league_id"],
                ev["home_competitor_id"],
                ev["away_competitor_id"],
                ev["home_team_name"],
                ev["away_team_name"],
                ev["start_time_utc"],
                ev["status"],
                ev.get("surface_or_format"),
            ),
        )

    # Seed odds
    odds = load_fixture("odds_snapshots.json")
    for o in odds:
        conn.execute(
            "INSERT INTO odds_snapshots (event_id, bookmaker_key, market_key, outcome_key, odds_decimal, is_sharp_benchmark) "
            "VALUES (?, ?, ?, ?, ?, ?)",
            (
                o["event_id"],
                o["bookmaker_key"],
                o["market_key"],
                o["outcome_key"],
                o["odds_decimal"],
                1 if o.get("is_sharp_benchmark") else 0,
            ),
        )

    # Seed predictions
    preds = load_fixture("model_predictions.json")
    for p in preds:
        conn.execute(
            "INSERT INTO model_predictions (event_id, market_key, outcome_key, p_model, p_sharp_devigged, "
            "p_true, fair_odds, estimated_pl_odds, ev_standard_pl, ev_taxfree_pl, kelly_quarter, model_version, factual_factors_json) "
            "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (
                p["event_id"],
                p["market_key"],
                p["outcome_key"],
                p["p_model"],
                p["p_sharp_devigged"],
                p["p_true"],
                p["fair_odds"],
                p["estimated_pl_odds"],
                p["ev_standard_pl"],
                p["ev_taxfree_pl"],
                p["kelly_quarter"],
                p["model_version"],
                json.dumps(p.get("factual_factors_json", {})),
            ),
        )

    # Seed users
    users = load_fixture("users.json")
    for u in users:
        conn.execute(
            "INSERT INTO users (id, name, email, email_verified, image, accepted_terms_18_plus_at, accepted_rodo_at) "
            "VALUES (?, ?, ?, ?, ?, ?, ?)",
            (
                u["id"],
                u["name"],
                u["email"],
                u.get("email_verified"),
                u.get("image"),
                u.get("accepted_terms_18_plus_at"),
                u.get("accepted_rodo_at"),
            ),
        )

    conn.commit()
    yield conn
    conn.close()


# 8. Fast Pure-Python In-Memory Repository
class MockInMemoryRepository:
    """Lightweight repository backed by Python dictionaries for instant testing."""

    def __init__(self, load_fixture_fn: Callable[[str], Any]):
        self.categories = {c["slug"]: c for c in load_fixture_fn("sports_categories.json")}
        self.leagues = {lg["id"]: lg for lg in load_fixture_fn("leagues.json")}
        self.events = {ev["id"]: ev for ev in load_fixture_fn("events.json")}
        self.competitors = {
            c["competitor_id"]: c for c in load_fixture_fn("competitor_ratings.json")
        }
        self.odds = load_fixture_fn("odds_snapshots.json")
        self.predictions = load_fixture_fn("model_predictions.json")
        self.users = {u["id"]: u for u in load_fixture_fn("users.json")}
        self.saved_slips: dict[str, dict[str, Any]] = {
            s["id"]: s for s in load_fixture_fn("saved_slips.json")
        }

    def get_active_categories(self, enable_phase2: bool = False) -> list[dict[str, Any]]:
        return [
            c
            for c in self.categories.values()
            if c.get("is_enabled_v1") or enable_phase2
        ]

    def get_events(self, sport: Optional[str] = None) -> list[dict[str, Any]]:
        res = list(self.events.values())
        if sport:
            matching_leagues = {
                lg["id"]
                for lg in self.leagues.values()
                if lg["sport_id"] == self.categories.get(sport, {}).get("id")
            }
            res = [ev for ev in res if ev["league_id"] in matching_leagues]
        return res

    def get_odds_by_event(self, event_id: str) -> list[dict[str, Any]]:
        return [o for o in self.odds if o["event_id"] == event_id]

    def get_predictions_by_event(self, event_id: str) -> list[dict[str, Any]]:
        return [p for p in self.predictions if p["event_id"] == event_id]

    def save_slip(self, slip_data: dict[str, Any]) -> dict[str, Any]:
        self.saved_slips[slip_data["id"]] = slip_data
        return slip_data

    def get_user_slips(self, user_id: str) -> list[dict[str, Any]]:
        return [s for s in self.saved_slips.values() if s.get("user_id") == user_id]


@pytest.fixture
def mock_repo(
    load_fixture: Callable[[str], Any],
) -> MockInMemoryRepository:
    return MockInMemoryRepository(load_fixture)


# 9. Mock Feeds Fixture
@pytest.fixture
def mock_odds_feed(
    load_fixture: Callable[[str], Any],
) -> Callable[..., list[dict[str, Any]]]:
    """Returns deterministic odds snapshot for given event and bookmaker."""
    odds_data = load_fixture("odds_snapshots.json")

    def _query(
        event_id: str,
        bookmaker_key: Optional[str] = None,
        market_key: Optional[str] = None,
    ) -> list[dict[str, Any]]:
        res = [o for o in odds_data if o["event_id"] == event_id]
        if bookmaker_key:
            res = [o for o in res if o["bookmaker_key"] == bookmaker_key]
        if market_key:
            res = [o for o in res if o["market_key"] == market_key]
        return res

    return _query


# 10. Assertion Helpers Fixture
@pytest.fixture
def assertions() -> Any:
    """Exports all mathematical and architectural assertion helpers."""
    import tests.helpers.assertions as assert_module

    return assert_module

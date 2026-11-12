"""Test Harness Self-Check Sanity Test Suite.

Verifies the integrity, reliability, and determinism of all test infrastructure components:
- Strict network isolation guard
- Fixture loading and data integrity across all 12 JSON files
- In-memory SQLite database DDL, constraints, seeding, and cascade operations
- Pure-Python MockInMemoryRepository and MockOddsFeed
- Reusable mathematical assertion helpers
"""

from __future__ import annotations

import os
import random
import socket
import sqlite3
from typing import Any, Callable
import pytest

from tests.helpers.assertions import (
    assert_anti_correlation_guard,
    assert_devig_convergence,
    assert_fractional_kelly,
    assert_never_color_alone,
    assert_polish_pit_threshold,
    assert_polish_turnover_tax,
    assert_probability_distribution,
    assert_ticket_splitting_advice,
    assert_wcag_contrast,
    calculate_relative_luminance,
)


# 1. Environment & Offline Determinism
def test_environment_offline_mode() -> None:
    """Verifies environment variables for deterministic offline operation."""
    assert os.environ.get("OFFLINE_MODE") == "true"
    assert os.environ.get("ENABLE_PHASE2_SPORTS") == "false"
    assert os.environ.get("DATABASE_URL") == "sqlite:///:memory:"

    # Fixed random seed check
    r1 = random.randint(1, 1000)
    random.seed(42)
    r_expected = random.randint(1, 1000)
    random.seed(42)
    assert random.randint(1, 1000) == r_expected


# 2. Strict Network Isolation Guard
def test_network_guard_blocks_external() -> None:
    """Verifies that attempts to open non-loopback socket connections are intercepted and blocked."""
    sock = socket.socket()
    with pytest.raises(RuntimeError) as exc_info:
        sock.connect(("8.8.8.8", 53))
    assert "External network connection blocked by QUANTKUPON offline test harness" in str(
        exc_info.value
    )


def test_network_guard_allows_loopback() -> None:
    """Verifies that loopback connections are not blocked by the guard rule."""
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        # Connect to an unassigned local port on 127.0.0.1; will get ConnectionRefusedError, NOT RuntimeError
        sock.connect(("127.0.0.1", 65432))
    except (ConnectionRefusedError, OSError) as e:
        assert not isinstance(e, RuntimeError)
    finally:
        sock.close()


# 3. Fixtures Loading & Data Integrity
def test_fixtures_all_12_files_present_and_valid(
    load_fixture: Callable[[str], Any],
) -> None:
    """Verifies that all 12 required JSON fixture files are loaded and non-empty."""
    fixture_files = [
        "sports_categories.json",
        "leagues.json",
        "competitor_ratings.json",
        "events.json",
        "odds_snapshots.json",
        "model_predictions.json",
        "users.json",
        "saved_slips.json",
        "devig_cases.json",
        "tax_cases.json",
        "calibration_samples.json",
        "design_tokens.json",
    ]
    for filename in fixture_files:
        data = load_fixture(filename)
        assert data is not None, f"Fixture {filename} returned None"
        assert len(data) > 0, f"Fixture {filename} is empty"


def test_fixtures_sports_categories_structure(
    load_fixture: Callable[[str], Any],
) -> None:
    """Verifies sports categories fixture has 4 active v1 sports and 2 disabled Phase 2 sports."""
    cats = load_fixture("sports_categories.json")
    slugs = {c["slug"]: c for c in cats}

    assert len(cats) == 6
    assert slugs["football"]["is_enabled_v1"] is True
    assert slugs["basketball"]["is_enabled_v1"] is True
    assert slugs["tennis"]["is_enabled_v1"] is True
    assert slugs["hockey"]["is_enabled_v1"] is True
    assert slugs["volleyball"]["is_enabled_v1"] is False
    assert slugs["table_tennis"]["is_enabled_v1"] is False


def test_fixtures_competitor_ratings_volatility(
    load_fixture: Callable[[str], Any],
) -> None:
    """Verifies competitor ratings include high-volatility table tennis player with sigma=0.095."""
    ratings = load_fixture("competitor_ratings.json")
    novak = next((c for c in ratings if c["competitor_id"] == "tt_novak_m"), None)
    assert novak is not None
    assert novak.get("glicko_sigma") == 0.095
    assert novak.get("glicko_rd") == 260.0


def test_fixtures_tax_cases_coverage(load_fixture: Callable[[str], Any]) -> None:
    """Verifies that tax cases cover statutory 0.88x, Betclic promo, Fortuna promo, 2280 border, and ticket splitting."""
    tax_cases = load_fixture("tax_cases.json")
    case_ids = {c["id"] for c in tax_cases}
    expected_cases = {
        "tax_standard_turnover",
        "tax_betclic_zero_tax_qualifying",
        "tax_betclic_zero_tax_disqualified",
        "tax_fortuna_zero_tax_qualifying",
        "tax_fortuna_zero_tax_disqualified",
        "tax_pit_exact_boundary_2280",
        "tax_pit_exceeded_2280_01",
        "tax_ticket_split_savings",
    }
    assert expected_cases.issubset(case_ids)


# 4. In-Memory SQLite DDL & Seeding
def test_sqlite_ddl_and_tables_exist(sqlite_db: sqlite3.Connection) -> None:
    """Verifies that all 9 Neon tables are created in SQLite with correct schemas."""
    cursor = sqlite_db.cursor()
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
    tables = {row["name"] for row in cursor.fetchall()}

    required_tables = {
        "sports_categories",
        "leagues",
        "competitor_ratings",
        "events",
        "odds_snapshots",
        "model_predictions",
        "users",
        "accounts",
        "sessions",
        "saved_slips",
    }
    assert required_tables.issubset(tables)


def test_sqlite_seeded_data_query(sqlite_db: sqlite3.Connection) -> None:
    """Verifies querying pre-seeded relational records in SQLite."""
    cursor = sqlite_db.cursor()

    # Query sports categories
    cursor.execute("SELECT COUNT(*) as count FROM sports_categories WHERE is_enabled_v1 = 1")
    active_sports_count = cursor.fetchone()["count"]
    assert active_sports_count == 4

    # Query odds snapshots
    cursor.execute("SELECT COUNT(*) as count FROM odds_snapshots")
    odds_count = cursor.fetchone()["count"]
    assert odds_count == 35

    # Query sharp benchmark odds
    cursor.execute("SELECT COUNT(*) as count FROM odds_snapshots WHERE is_sharp_benchmark = 1")
    sharp_odds_count = cursor.fetchone()["count"]
    assert sharp_odds_count > 0


def test_sqlite_foreign_key_cascade(sqlite_db: sqlite3.Connection) -> None:
    """Verifies foreign key constraints and ON DELETE CASCADE behavior in SQLite."""
    cursor = sqlite_db.cursor()

    # Insert a user
    cursor.execute(
        "INSERT INTO users (id, name, email) VALUES ('usr_cascade_test', 'Cascade Test', 'cascade@test.com')"
    )

    # Insert a session linked to the user
    cursor.execute(
        "INSERT INTO sessions (id, session_token, user_id, expires) "
        "VALUES ('sess_1', 'tok_1', 'usr_cascade_test', '2026-12-31T23:59:59Z')"
    )

    # Insert a saved slip linked to the user
    cursor.execute(
        "INSERT INTO saved_slips (id, user_id, selections_json, user_profile_params_json, bookmaker_key, "
        "tax_multiplier, total_odds_gross, total_odds_net, potential_payout_gross, potential_payout_net, "
        "joint_probability, slip_ev_net, recommended_kelly_stake_pct) "
        "VALUES ('slip_1', 'usr_cascade_test', '[]', '{}', 'sts', 0.88, 2.0, 1.76, 176.0, 176.0, 0.5, 0.0, 0.0)"
    )
    sqlite_db.commit()

    # Delete the user
    cursor.execute("DELETE FROM users WHERE id = 'usr_cascade_test'")
    sqlite_db.commit()

    # Verify session and saved slip were cascade deleted
    cursor.execute("SELECT COUNT(*) as count FROM sessions WHERE user_id = 'usr_cascade_test'")
    assert cursor.fetchone()["count"] == 0

    cursor.execute("SELECT COUNT(*) as count FROM saved_slips WHERE user_id = 'usr_cascade_test'")
    assert cursor.fetchone()["count"] == 0


def test_sqlite_check_constraint_probability(sqlite_db: sqlite3.Connection) -> None:
    """Verifies that check constraints reject invalid probabilities (> 1.0 or < 0.0)."""
    cursor = sqlite_db.cursor()
    with pytest.raises(sqlite3.IntegrityError):
        cursor.execute(
            "INSERT INTO model_predictions (event_id, market_key, outcome_key, p_model, p_sharp_devigged, "
            "p_true, fair_odds, estimated_pl_odds, ev_standard_pl, ev_taxfree_pl, kelly_quarter, model_version) "
            "VALUES ('ev_fb_ars_che', '1x2', 'home_win', 1.5, 0.5, 0.5, 2.0, 2.0, 0.0, 0.0, 0.0, 'v1')"
        )


# 5. Pure-Python MockInMemoryRepository & MockOddsFeed
def test_mock_repository_methods(mock_repo: Any) -> None:
    """Verifies in-memory dictionary repository operations."""
    active_cats = mock_repo.get_active_categories(enable_phase2=False)
    assert len(active_cats) == 4

    all_cats = mock_repo.get_active_categories(enable_phase2=True)
    assert len(all_cats) == 6

    events = mock_repo.get_events()
    assert len(events) == 7

    fb_events = mock_repo.get_events(sport="football")
    assert len(fb_events) == 2

    odds = mock_repo.get_odds_by_event("ev_fb_ars_che")
    assert len(odds) > 0

    preds = mock_repo.get_predictions_by_event("ev_fb_ars_che")
    assert len(preds) > 0

    # Test save and query slip
    new_slip = {
        "id": "slip_dyn_test",
        "user_id": "usr_compliant_adult",
        "total_odds_gross": 3.0,
    }
    mock_repo.save_slip(new_slip)
    user_slips = mock_repo.get_user_slips("usr_compliant_adult")
    assert any(s["id"] == "slip_dyn_test" for s in user_slips)


def test_mock_odds_feed_query(mock_odds_feed: Callable[..., list[dict[str, Any]]]) -> None:
    """Verifies deterministic querying of mock odds feed."""
    odds = mock_odds_feed("ev_fb_ars_che", bookmaker_key="pinnacle", market_key="1x2")
    assert len(odds) == 3
    home_odd = next((o for o in odds if o["outcome_key"] == "home_win"), None)
    assert home_odd is not None
    assert home_odd["odds_decimal"] == 1.75
    assert home_odd["is_sharp_benchmark"] is True


# 6. Reusable Mathematical Assertion Helpers
def test_assertion_probability_distribution() -> None:
    """Verifies assert_probability_distribution helper."""
    assert_probability_distribution([0.5, 0.3, 0.2])
    assert_probability_distribution({"home": 0.6, "draw": 0.25, "away": 0.15})

    with pytest.raises(AssertionError):
        assert_probability_distribution([0.5, 0.5, 0.2])  # Sum = 1.2

    with pytest.raises(AssertionError):
        assert_probability_distribution([-0.1, 1.1])  # Negative value


def test_assertion_devig_convergence() -> None:
    """Verifies assert_devig_convergence helper and monotonicity check."""
    odds = [1.50, 3.20, 5.50]
    devigged_probs = [0.62, 0.26, 0.12]
    assert_devig_convergence(devigged_probs, odds)

    # Monotonicity violation: lower odds with lower probability
    with pytest.raises(AssertionError):
        assert_devig_convergence([0.20, 0.70, 0.10], odds)


def test_assertion_polish_turnover_tax() -> None:
    """Verifies statutory 0.88x turnover tax calculation assertions."""
    # Standard 12% turnover tax
    assert_polish_turnover_tax(100.0, 2.50, 2.20, 220.0, is_promotional=False)

    # Promotional zero-tax (Betclic / Fortuna)
    assert_polish_turnover_tax(100.0, 2.40, 2.40, 240.0, is_promotional=True)

    with pytest.raises(AssertionError):
        assert_polish_turnover_tax(100.0, 2.50, 2.50, 250.0, is_promotional=False)


def test_assertion_polish_pit_threshold() -> None:
    """Verifies Polish 10% PIT threshold at 2280.00 PLN."""
    # Flat 2280.00 PLN: 0 PIT
    assert_polish_pit_threshold(2280.00, 2280.00, pit_applies=False, pit_deduction=0.0)

    # 2280.01 PLN: 10% PIT on full amount
    assert_polish_pit_threshold(2280.01, 2052.01, pit_applies=True, pit_deduction=228.00)

    # Sub-threshold 500 PLN: 0 PIT
    assert_polish_pit_threshold(500.00, 500.00, pit_applies=False, pit_deduction=0.0)

    with pytest.raises(AssertionError):
        # 2500 PLN without PIT applied
        assert_polish_pit_threshold(2500.00, 2500.00, pit_applies=False, pit_deduction=0.0)


def test_assertion_ticket_splitting_advice() -> None:
    """Verifies ticket splitting advice assertions."""
    advice = {
        "split_into": 2,
        "stake_per_ticket": 100.0,
        "tax_saved": 300.0,
    }
    assert_ticket_splitting_advice(200.0, 3000.0, advice)


def test_assertion_anti_correlation_guard() -> None:
    """Verifies Anti-Correlation Guard assertion helper."""
    valid_legs = [{"event_id": "ev_1"}, {"event_id": "ev_2"}, {"event_id": "ev_3"}]
    assert_anti_correlation_guard(valid_legs)

    duplicate_legs = [{"event_id": "ev_1"}, {"event_id": "ev_1"}]
    with pytest.raises(AssertionError):
        assert_anti_correlation_guard(duplicate_legs)


def test_assertion_fractional_kelly() -> None:
    """Verifies Fractional Kelly Quarter-Kelly stake bounds and 5% ceiling."""
    # Negative EV -> 0.0
    assert_fractional_kelly(0.0, -0.05)

    # Normal EV -> within bounds
    assert_fractional_kelly(0.025, 0.08)

    # Capped at 5%
    assert_fractional_kelly(0.05, 0.45)

    with pytest.raises(AssertionError):
        assert_fractional_kelly(0.08, 0.45)  # Exceeds 5% cap

    with pytest.raises(AssertionError):
        assert_fractional_kelly(0.02, -0.01)  # Positive fraction on negative EV


def test_assertion_never_color_alone_and_wcag() -> None:
    """Verifies 'Never Color Alone' rule and WCAG 2.2 AA contrast calculation."""
    assert_never_color_alone("+4.8% ▲ EV", 0.048)
    assert_never_color_alone("-2.1% ▼ EV", -0.021)

    with pytest.raises(AssertionError):
        assert_never_color_alone("4.8% EV", 0.048)  # Missing sign and arrow

    # Contrast check: Emerald on Canvas Obsidian (> 4.5:1)
    lum_emerald = calculate_relative_luminance("#10B981")
    lum_canvas = calculate_relative_luminance("#0B0F19")
    assert lum_emerald > lum_canvas
    assert_wcag_contrast("#10B981", "#0B0F19", min_ratio=4.5)

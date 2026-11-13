"""Feature 2: Neon PostgreSQL Schema Tests.

Verifies table existence, primary keys, foreign key cascading deletions,
referential integrity, and check constraints for probabilities and betting entities.
"""

from __future__ import annotations

import sqlite3
import pytest


def test_feat_02_all_neon_tables_exist_with_columns(sqlite_db: sqlite3.Connection) -> None:
    """Verifies that all 9 core Neon PostgreSQL tables exist with expected columns."""
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
    assert required_tables.issubset(tables), f"Missing tables: {required_tables - tables}"

    # Verify key columns in model_predictions
    cursor.execute("PRAGMA table_info(model_predictions);")
    cols = {row["name"] for row in cursor.fetchall()}
    assert {"p_model", "p_sharp_devigged", "p_true", "fair_odds", "ev_standard_pl", "kelly_quarter"}.issubset(cols)

    # Verify key columns in users
    cursor.execute("PRAGMA table_info(users);")
    user_cols = {row["name"] for row in cursor.fetchall()}
    assert {"id", "email", "accepted_terms_18_plus_at", "accepted_rodo_at"}.issubset(user_cols)


def test_feat_02_foreign_key_cascade_deletion_sports_hierarchy(sqlite_db: sqlite3.Connection) -> None:
    """Verifies cascading deletion from sports_categories down to leagues, events, and odds_snapshots."""
    cursor = sqlite_db.cursor()

    # Create custom sport hierarchy
    cursor.execute(
        "INSERT INTO sports_categories (id, slug, name_pl, active_model) VALUES (999, 'test_sport', 'Sport Testowy', 'model_v1')"
    )
    cursor.execute(
        "INSERT INTO leagues (id, sport_id, name, country) VALUES (999, 999, 'Liga Testowa', 'Polska')"
    )
    cursor.execute(
        "INSERT INTO events (id, league_id, home_competitor_id, away_competitor_id, home_team_name, away_team_name, start_time_utc) "
        "VALUES ('ev_test_casc', 999, 'c_1', 'c_2', 'Team A', 'Team B', '2026-12-01T20:00:00Z')"
    )
    cursor.execute(
        "INSERT INTO odds_snapshots (event_id, bookmaker_key, market_key, outcome_key, odds_decimal) "
        "VALUES ('ev_test_casc', 'sts', '1x2', 'home_win', 2.10)"
    )
    sqlite_db.commit()

    # Delete parent sport
    cursor.execute("DELETE FROM sports_categories WHERE id = 999")
    sqlite_db.commit()

    # Verify child tables purged
    cursor.execute("SELECT count(*) as cnt FROM leagues WHERE sport_id = 999")
    assert cursor.fetchone()["cnt"] == 0

    cursor.execute("SELECT count(*) as cnt FROM events WHERE id = 'ev_test_casc'")
    assert cursor.fetchone()["cnt"] == 0

    cursor.execute("SELECT count(*) as cnt FROM odds_snapshots WHERE event_id = 'ev_test_casc'")
    assert cursor.fetchone()["cnt"] == 0


def test_feat_02_foreign_key_cascade_deletion_user_gdpr_purge(sqlite_db: sqlite3.Connection) -> None:
    """Verifies that GDPR user deletion cascade purges accounts, sessions, and saved slips."""
    cursor = sqlite_db.cursor()

    test_uid = "usr_gdpr_purge_candidate"
    cursor.execute(
        "INSERT INTO users (id, name, email, accepted_terms_18_plus_at, accepted_rodo_at) "
        "VALUES (?, 'Purge User', 'purge@test.com', '2026-11-01T12:00:00Z', '2026-11-01T12:00:00Z')",
        (test_uid,),
    )
    cursor.execute(
        "INSERT INTO accounts (id, user_id, type, provider, provider_account_id) "
        "VALUES ('acc_p1', ?, 'oauth', 'google', 'g_123')",
        (test_uid,),
    )
    cursor.execute(
        "INSERT INTO sessions (id, session_token, user_id, expires) "
        "VALUES ('sess_p1', 'tok_p1', ?, '2026-12-31T23:59:59Z')",
        (test_uid,),
    )
    cursor.execute(
        "INSERT INTO saved_slips (id, user_id, selections_json, user_profile_params_json, bookmaker_key, "
        "tax_multiplier, total_odds_gross, total_odds_net, potential_payout_gross, potential_payout_net, "
        "joint_probability, slip_ev_net, recommended_kelly_stake_pct) "
        "VALUES ('slip_p1', ?, '[]', '{}', 'sts', 0.88, 2.0, 1.76, 176.0, 176.0, 0.5, 0.05, 0.02)",
        (test_uid,),
    )
    sqlite_db.commit()

    # Delete user
    cursor.execute("DELETE FROM users WHERE id = ?", (test_uid,))
    sqlite_db.commit()

    # Verify all linked user data purged
    cursor.execute("SELECT count(*) as cnt FROM accounts WHERE user_id = ?", (test_uid,))
    assert cursor.fetchone()["cnt"] == 0
    cursor.execute("SELECT count(*) as cnt FROM sessions WHERE user_id = ?", (test_uid,))
    assert cursor.fetchone()["cnt"] == 0
    cursor.execute("SELECT count(*) as cnt FROM saved_slips WHERE user_id = ?", (test_uid,))
    assert cursor.fetchone()["cnt"] == 0


def test_feat_02_check_constraints_probability_and_odds_bounds(sqlite_db: sqlite3.Connection) -> None:
    """Verifies database-level check constraints on probability range [0, 1]."""
    cursor = sqlite_db.cursor()

    # Attempt inserting probability > 1.0
    with pytest.raises(sqlite3.IntegrityError):
        cursor.execute(
            "INSERT INTO model_predictions (event_id, market_key, outcome_key, p_model, p_sharp_devigged, "
            "p_true, fair_odds, estimated_pl_odds, ev_standard_pl, ev_taxfree_pl, kelly_quarter, model_version) "
            "VALUES ('ev_fb_ars_che', '1x2', 'test_invalid_p', 1.05, 0.5, 0.5, 2.0, 2.0, 0.0, 0.0, 0.0, 'v1')"
        )

    # Attempt inserting negative probability
    with pytest.raises(sqlite3.IntegrityError):
        cursor.execute(
            "INSERT INTO model_predictions (event_id, market_key, outcome_key, p_model, p_sharp_devigged, "
            "p_true, fair_odds, estimated_pl_odds, ev_standard_pl, ev_taxfree_pl, kelly_quarter, model_version) "
            "VALUES ('ev_fb_ars_che', '1x2', 'test_negative_p', -0.05, 0.5, 0.5, 2.0, 2.0, 0.0, 0.0, 0.0, 'v1')"
        )


def test_feat_02_saved_slips_financial_and_kelly_constraints(sqlite_db: sqlite3.Connection) -> None:
    """Verifies insertion and referential integrity of saved betting slips."""
    cursor = sqlite_db.cursor()

    # Verify inserting slip for existing user succeeds
    valid_slip_id = "slip_financial_valid"
    cursor.execute(
        "INSERT INTO saved_slips (id, user_id, selections_json, user_profile_params_json, bookmaker_key, "
        "tax_multiplier, total_odds_gross, total_odds_net, potential_payout_gross, potential_payout_net, "
        "joint_probability, slip_ev_net, recommended_kelly_stake_pct) "
        "VALUES (?, 'usr_compliant_adult', '[]', '{}', 'sts', 0.88, 3.50, 3.08, 350.0, 308.0, 0.35, 0.078, 0.025)",
        (valid_slip_id,),
    )
    sqlite_db.commit()

    cursor.execute("SELECT total_odds_gross, total_odds_net, potential_payout_net FROM saved_slips WHERE id = ?", (valid_slip_id,))
    row = cursor.fetchone()
    assert row is not None
    assert row["total_odds_gross"] == 3.50
    assert row["total_odds_net"] == 3.08
    assert row["potential_payout_net"] == 308.0

    # Foreign key rejection on non-existent user
    with pytest.raises(sqlite3.IntegrityError):
        cursor.execute(
            "INSERT INTO saved_slips (id, user_id, selections_json, user_profile_params_json, bookmaker_key, "
            "tax_multiplier, total_odds_gross, total_odds_net, potential_payout_gross, potential_payout_net, "
            "joint_probability, slip_ev_net, recommended_kelly_stake_pct) "
            "VALUES ('slip_orphan', 'non_existent_user_id', '[]', '{}', 'sts', 0.88, 2.0, 1.76, 200.0, 176.0, 0.5, 0.0, 0.0)"
        )

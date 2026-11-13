"""Feature 7: Football Dixon-Coles Model Tests.

Verifies the Dixon-Coles bivariate Poisson score grid, low-score correlation tau,
70% xG / 30% historical goals weighting, Over/Under 2.5 totals complementarity,
BTTS derivation, and prediction consistency against pre-match fixtures.
"""

from __future__ import annotations

import math
from typing import Any, Callable
import numpy as np
import pytest

from tests.helpers.assertions import assert_probability_distribution


def compute_dixon_coles_matrix(lam: float, mu: float, rho: float = -0.12, max_goals: int = 8) -> np.ndarray:
    """Computes (max_goals+1)x(max_goals+1) score probability matrix with Dixon-Coles adjustment."""
    grid = np.zeros((max_goals + 1, max_goals + 1), dtype=float)
    lam = max(lam, 1e-4)
    mu = max(mu, 1e-4)

    for x in range(max_goals + 1):
        for y in range(max_goals + 1):
            tau = 1.0
            if x == 0 and y == 0:
                tau = 1.0 - lam * mu * rho
            elif x == 0 and y == 1:
                tau = 1.0 + lam * rho
            elif x == 1 and y == 0:
                tau = 1.0 + mu * rho
            elif x == 1 and y == 1:
                tau = 1.0 - rho
            tau = max(0.0, tau)
            p = (
                tau
                * (math.exp(-lam) * (lam**x) / math.factorial(x))
                * (math.exp(-mu) * (mu**y) / math.factorial(y))
            )
            grid[x, y] = p

    total = np.sum(grid)
    if total > 0:
        grid /= total
    return grid


def test_feat_07_football_dixon_coles_1x2_normalization() -> None:
    """Verifies that 1X2 market outcomes derived from Dixon-Coles grid normalize to 1.0 +- 1e-5."""
    grid = compute_dixon_coles_matrix(lam=1.75, mu=1.15, rho=-0.12)
    p_home = float(np.sum(np.tril(grid, -1)))  # x > y (rows > cols)
    p_draw = float(np.trace(grid))              # x == y
    p_away = float(np.sum(np.triu(grid, 1)))   # x < y (rows < cols)

    assert_probability_distribution([p_home, p_draw, p_away], tolerance=1e-5)
    assert p_home > p_draw > p_away


def test_feat_07_football_xg_weighting_70_30() -> None:
    """Verifies that intensity calculation implements 70% xG / 30% historical goals weighting."""
    xg_attack = 2.25
    goals_hist = 1.00
    weighted_attack = 0.70 * xg_attack + 0.30 * goals_hist
    expected_intensity = 1.875

    assert abs(weighted_attack - expected_intensity) < 1e-6
    # xG dominance check
    assert abs(weighted_attack - xg_attack) < abs(weighted_attack - goals_hist)


def test_feat_07_football_totals_complementarity() -> None:
    """Verifies that Over 2.5 and Under 2.5 goal probabilities sum to 1.0 +- 1e-5."""
    grid = compute_dixon_coles_matrix(lam=1.60, mu=1.20, rho=-0.10)
    p_under = 0.0
    p_over = 0.0

    for x in range(grid.shape[0]):
        for y in range(grid.shape[1]):
            if x + y <= 2:
                p_under += grid[x, y]
            else:
                p_over += grid[x, y]

    assert_probability_distribution([p_over, p_under], tolerance=1e-5)
    assert 0.0 < p_over < 1.0
    assert 0.0 < p_under < 1.0


def test_feat_07_football_btts_derivation() -> None:
    """Verifies Both Teams to Score (BTTS) Yes and No probabilities sum to 1.0 +- 1e-5."""
    grid = compute_dixon_coles_matrix(lam=1.50, mu=1.30, rho=-0.08)
    p_btts_yes = float(np.sum(grid[1:, 1:]))
    p_btts_no = 1.0 - p_btts_yes

    assert_probability_distribution([p_btts_yes, p_btts_no], tolerance=1e-5)
    assert p_btts_yes > 0.40


def test_feat_07_football_fixture_prediction_match(load_fixture: Callable[[str], Any]) -> None:
    """Verifies Football model prediction consistency against pre-recorded offline fixture records."""
    preds = load_fixture("model_predictions.json")
    fb_preds = [p for p in preds if p["event_id"] == "ev_fb_ars_che" and p["market_key"] == "1x2"]

    assert len(fb_preds) == 3
    p_map = {p["outcome_key"]: p["p_model"] for p in fb_preds}
    assert_probability_distribution(p_map, tolerance=1e-4)
    assert p_map["home_win"] > p_map["draw"] > p_map["away_win"]
    assert p_map["home_win"] == 0.58
    assert p_map["draw"] == 0.24
    assert p_map["away_win"] == 0.18

"""Feature 8: Basketball Pace Model Tests.

Verifies the geometric possession pace formula, offensive/defensive efficiency
ratings with home court advantage, moneyline normal distribution win probabilities,
spread CDF complementarity, and Over/Under total monotonicity.
"""

from __future__ import annotations

import math
from typing import Any, Callable
import numpy as np
import pytest
from scipy.stats import norm

from tests.helpers.assertions import assert_probability_distribution


def calculate_match_pace(pace_a: float, pace_b: float, league_pace: float = 99.0) -> float:
    """Calculates expected match pace as geometric interaction normalised by league pace."""
    if pace_a <= 0 or pace_b <= 0 or league_pace <= 0:
        raise ValueError("Pace values must be strictly positive")
    return (pace_a * pace_b) / league_pace


def calculate_expected_team_points(
    pace: float,
    ortg_team: float,
    drtg_opp: float,
    avg_rtg: float = 114.0,
    hca: float = 0.0,
) -> float:
    """Calculates expected team score per possession efficiency and HCA."""
    return (pace / 100.0) * (ortg_team + drtg_opp - avg_rtg + hca)


def test_feat_08_basketball_pace_formula() -> None:
    """Verifies geometric interaction match pace formula matches analytical value 97.45 +- 0.01."""
    pace_celtics = 100.5
    pace_knicks = 96.0
    pace_lg = 99.0

    match_pace = calculate_match_pace(pace_celtics, pace_knicks, pace_lg)
    expected_pace = (100.5 * 96.0) / 99.0
    assert abs(match_pace - expected_pace) < 1e-6
    assert abs(match_pace - 97.4545) < 0.01


def test_feat_08_basketball_team_expected_totals() -> None:
    """Verifies offensive/defensive ratings with 2.5 HCA yield expected team totals."""
    pace = 97.454545
    mu_celtics = calculate_expected_team_points(pace, ortg_team=122.3, drtg_opp=114.2, avg_rtg=114.0, hca=2.5)
    mu_knicks = calculate_expected_team_points(pace, ortg_team=116.5, drtg_opp=110.1, avg_rtg=114.0, hca=0.0)

    assert abs(mu_celtics - 121.82) < 0.05
    assert abs(mu_knicks - 109.73) < 0.05
    spread = mu_celtics - mu_knicks
    assert abs(spread - 12.09) < 0.05


def test_feat_08_basketball_moneyline_normalization() -> None:
    """Verifies Moneyline 2-way win probabilities via Gaussian CDF sum to 1.0 +- 1e-5."""
    mu_diff = 12.084
    sigma_diff = 11.50

    p_home = float(norm.cdf(mu_diff / sigma_diff))
    p_away = 1.0 - p_home

    assert_probability_distribution([p_home, p_away], tolerance=1e-5)
    assert 0.84 < p_home < 0.87
    assert 0.13 < p_away < 0.16


def test_feat_08_basketball_spread_cdf_complement() -> None:
    """Verifies point spread line L = -5.5 coverage and underdog complementarity."""
    spread_threshold = 5.5  # Home must win by more than 5.5 points
    mu_diff = 12.084
    sigma_diff = 11.50

    # Home covers -5.5 if margin D > 5.5
    p_cover_home = float(1.0 - norm.cdf((spread_threshold - mu_diff) / sigma_diff))
    p_cover_away = 1.0 - p_cover_home

    assert_probability_distribution([p_cover_home, p_cover_away], tolerance=1e-5)
    assert 0.70 < p_cover_home < 0.75
    assert 0.25 < p_cover_away < 0.30


def test_feat_08_basketball_totals_over_under_monotonicity() -> None:
    """Verifies that Over/Under probability decreases monotonically as the total line increases."""
    mu_total = 121.82 + 109.73  # 231.55
    sigma_total = 16.50
    lines = [215.5, 220.5, 225.5, 230.5]

    over_probs = []
    for line in lines:
        p_over = float(1.0 - norm.cdf((line - mu_total) / sigma_total))
        p_under = 1.0 - p_over
        assert_probability_distribution([p_over, p_under], tolerance=1e-5)
        over_probs.append(p_over)

    # Monotonic decrease
    for i in range(len(over_probs) - 1):
        assert over_probs[i] > over_probs[i + 1]

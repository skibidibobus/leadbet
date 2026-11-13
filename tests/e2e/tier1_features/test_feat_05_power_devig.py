"""Feature 5: De-vigging (Power Method) Tests.

Verifies the Power method (Clarke 1993) across fair markets, symmetric spreads,
balanced 3-way markets, high-overround lines, and multi-outcome 4-way markets.
"""

from __future__ import annotations

from typing import Any, Callable
import numpy as np
import pytest
from scipy.optimize import brentq

from tests.helpers.assertions import assert_devig_convergence, assert_probability_distribution


def devig_power(odds: list[float]) -> tuple[list[float], float]:
    """Reference implementation of Power de-vigging method.

    Solves for exponent c in [0.5, 3.0] such that sum((1/O_i)^c) == 1.0.
    """
    arr = np.array(odds, dtype=float)
    if np.any(arr <= 1.0):
        raise ValueError("Odds must be strictly greater than 1.0")

    inv_odds = 1.0 / arr
    sum_inv = float(np.sum(inv_odds))
    if abs(sum_inv - 1.0) < 1e-9:
        return inv_odds.tolist(), 1.0

    def f(c: float) -> float:
        return float(np.sum(inv_odds**c) - 1.0)

    c_star = float(brentq(f, 0.5, 3.0))
    p_star = inv_odds**c_star
    p_normalized = p_star / np.sum(p_star)
    return p_normalized.tolist(), c_star


def test_feat_05_power_fair_market_boundary() -> None:
    """Verifies that in a zero-overround fair market, the power exponent c equals 1.000000 exactly."""
    odds = [2.00, 2.00]
    probs, c = devig_power(odds)

    assert abs(c - 1.0) < 1e-5
    assert_probability_distribution(probs)
    assert abs(probs[0] - 0.50) < 1e-6
    assert abs(probs[1] - 0.50) < 1e-6


def test_feat_05_power_2way_symmetric_spread(load_fixture: Callable[[str], Any]) -> None:
    """Verifies Power method solves symmetric spread with exponent c > 1.0 preserving 50/50 split."""
    cases = {c["id"]: c for c in load_fixture("devig_cases.json")}
    case = cases["devig_2way_even"]
    odds = case["odds"]

    probs, c = devig_power(odds)
    assert_devig_convergence(probs, odds, method="power", tolerance=1e-5)
    assert c > 1.0
    assert abs(probs[0] - 0.50) < 1e-4
    assert abs(probs[1] - 0.50) < 1e-4


def test_feat_05_power_3way_balanced_football(load_fixture: Callable[[str], Any]) -> None:
    """Verifies Power method on balanced 3-way odds yields monotonic fair probabilities and valid exponent."""
    cases = {c["id"]: c for c in load_fixture("devig_cases.json")}
    case = cases["devig_3way_balanced"]
    odds = case["odds"]

    probs, c = devig_power(odds)
    assert_devig_convergence(probs, odds, method="power", tolerance=1e-5)
    assert 1.04 <= c <= 1.15
    # Odds [2.60, 3.20, 2.70] -> lowest odds 2.60 has highest prob, highest odds 3.20 has lowest
    assert probs[0] > probs[2] > probs[1]


def test_feat_05_power_high_overround_retail(load_fixture: Callable[[str], Any]) -> None:
    """Verifies Power method on high-margin retail market (overround > 11%) converges stably."""
    cases = {c["id"]: c for c in load_fixture("devig_cases.json")}
    case = cases["devig_high_overround"]
    odds = case["odds"]

    probs, c = devig_power(odds)
    assert_devig_convergence(probs, odds, method="power", tolerance=1e-5)
    assert abs(probs[0] - 0.50) < 1e-4
    assert abs(probs[1] - 0.50) < 1e-4
    assert 1.15 <= c <= 1.25


def test_feat_05_power_multi_outcome_4way(load_fixture: Callable[[str], Any]) -> None:
    """Verifies Power method across 4-way outright market satisfies probability sum and order monotonicity."""
    cases = {c["id"]: c for c in load_fixture("devig_cases.json")}
    case = cases["devig_multi_outcome_4way"]
    odds = case["odds"]

    probs, c = devig_power(odds)
    assert_devig_convergence(probs, odds, method="power", tolerance=1e-5)
    assert 1.05 <= c <= 1.25
    assert probs[0] > probs[1] > probs[2] > probs[3]

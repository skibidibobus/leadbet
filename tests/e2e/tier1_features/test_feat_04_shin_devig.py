"""Feature 4: De-vigging (Shin Method) Tests.

Verifies Shin's insider trading model de-vigging across 2-way symmetric,
2-way asymmetric, 3-way football, extreme favorite-longshot markets,
and favorite-longshot bias correction relative to proportional scaling.
"""

from __future__ import annotations

from typing import Any, Callable
import numpy as np
import pytest
from scipy.optimize import brentq

from tests.helpers.assertions import assert_devig_convergence, assert_probability_distribution


def devig_shin(odds: list[float]) -> tuple[list[float], float]:
    """Reference implementation of Shin's (1993) de-vigging method.

    Solves for insider proportion z in [0, 0.5] such that sum(p_i) == 1.0.
    """
    arr = np.array(odds, dtype=float)
    if np.any(arr <= 1.0):
        raise ValueError("Odds must be strictly greater than 1.0")

    pi = 1.0 / arr
    sum_pi = float(np.sum(pi))
    if abs(sum_pi - 1.0) < 1e-9:
        return (pi / sum_pi).tolist(), 0.0

    def f(z: float) -> float:
        p = (np.sqrt(z**2 + 4.0 * (1.0 - z) * (pi**2 / sum_pi)) - z) / (2.0 * (1.0 - z))
        return float(np.sum(p) - 1.0)

    z_star = float(brentq(f, 0.0, 0.499))
    p_star = (np.sqrt(z_star**2 + 4.0 * (1.0 - z_star) * (pi**2 / sum_pi)) - z_star) / (
        2.0 * (1.0 - z_star)
    )
    p_normalized = p_star / np.sum(p_star)
    return p_normalized.tolist(), z_star


def devig_multiplicative(odds: list[float]) -> list[float]:
    arr = np.array(odds, dtype=float)
    pi = 1.0 / arr
    return (pi / np.sum(pi)).tolist()


def test_feat_04_shin_2way_symmetric(load_fixture: Callable[[str], Any]) -> None:
    """Verifies Shin method on balanced 2-way market yields exact 50/50 probability."""
    cases = {c["id"]: c for c in load_fixture("devig_cases.json")}
    case = cases["devig_2way_even"]
    odds = case["odds"]

    probs, z = devig_shin(odds)
    assert_devig_convergence(probs, odds, method="shin", tolerance=1e-5)
    assert abs(probs[0] - 0.50) < 1e-4
    assert abs(probs[1] - 0.50) < 1e-4
    assert abs(probs[0] - probs[1]) < 1e-6
    assert 0.01 <= z <= 0.05


def test_feat_04_shin_2way_asymmetric(load_fixture: Callable[[str], Any]) -> None:
    """Verifies Shin method preserves strict monotonicity and distribution invariants on uneven 2-way."""
    cases = {c["id"]: c for c in load_fixture("devig_cases.json")}
    case = cases["devig_2way_uneven"]
    odds = case["odds"]

    probs, z = devig_shin(odds)
    assert_devig_convergence(probs, odds, method="shin", tolerance=1e-5)
    assert probs[0] > probs[1]
    assert 0.65 < probs[0] < 0.75
    assert 0.25 < probs[1] < 0.35


def test_feat_04_shin_3way_football_standard(load_fixture: Callable[[str], Any]) -> None:
    """Verifies Shin method on standard 1X2 market converges to expected probability vector."""
    cases = {c["id"]: c for c in load_fixture("devig_cases.json")}
    case = cases["devig_3way_football_standard"]
    odds = case["odds"]

    probs, z = devig_shin(odds)
    assert_devig_convergence(probs, odds, method="shin", tolerance=1e-5)
    z_min, z_max = case["expected_shin_z_range"]
    assert z_min <= z <= z_max
    assert probs[0] > probs[1] > probs[2]
    assert abs(probs[0] - 0.525) < 0.02


def test_feat_04_shin_extreme_favorite_longshot(load_fixture: Callable[[str], Any]) -> None:
    """Verifies Shin method numerical stability on extreme favorite vs longshot (1.02 vs 35.0)."""
    cases = {c["id"]: c for c in load_fixture("devig_cases.json")}
    case = cases["devig_extreme_favorite_longshot"]
    odds = case["odds"]

    probs, z = devig_shin(odds)
    assert_devig_convergence(probs, odds, method="shin", tolerance=1e-5)
    z_min, z_max = case["expected_shin_z_range"]
    assert z_min <= z <= z_max
    assert probs[0] > 0.970
    assert probs[1] < 0.030


def test_feat_04_shin_favorite_longshot_bias_correction() -> None:
    """Verifies that Shin method corrects favorite-longshot bias more aggressively than proportional devig."""
    odds = [1.15, 5.50]
    p_shin, z = devig_shin(odds)
    p_mult = devig_multiplicative(odds)

    assert_devig_convergence(p_shin, odds, method="shin")
    # Favorite has higher probability under Shin than multiplicative, longshot has lower
    assert p_shin[0] > p_mult[0], f"Shin {p_shin[0]} must exceed Multiplicative {p_mult[0]} on favorite"
    assert p_shin[1] < p_mult[1], f"Shin {p_shin[1]} must be lower than Multiplicative {p_mult[1]} on longshot"

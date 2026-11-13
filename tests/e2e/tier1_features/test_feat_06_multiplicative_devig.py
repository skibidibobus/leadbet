"""Feature 6: De-vigging (Multiplicative Method) Tests.

Verifies proportional normalization baseline across symmetric 2-way lines,
ratio preservation invariance, standard 3-way football markets, low-margin sharp lines,
and multi-selection group betting lines.
"""

from __future__ import annotations

from typing import Any, Callable
import numpy as np
import pytest

from tests.helpers.assertions import assert_devig_convergence, assert_probability_distribution


def devig_multiplicative(odds: list[float]) -> list[float]:
    """Reference implementation of proportional Multiplicative de-vigging."""
    arr = np.array(odds, dtype=float)
    if np.any(arr <= 1.0):
        raise ValueError("Odds must be strictly greater than 1.0")
    pi = 1.0 / arr
    return (pi / np.sum(pi)).tolist()


def test_feat_06_multiplicative_2way_even() -> None:
    """Verifies that 2-way symmetric odds [1.90, 1.90] devig to exact [0.50, 0.50]."""
    odds = [1.90, 1.90]
    probs = devig_multiplicative(odds)

    assert_devig_convergence(probs, odds, method="multiplicative")
    assert abs(probs[0] - 0.50) < 1e-6
    assert abs(probs[1] - 0.50) < 1e-6


def test_feat_06_multiplicative_ratio_preservation() -> None:
    """Verifies that proportional devig strictly preserves the inverse odds ratio."""
    odds = [1.50, 3.00]
    probs = devig_multiplicative(odds)

    assert_probability_distribution(probs)
    # Ratio p_0 / p_1 == 3.00 / 1.50 == 2.000000 exactly
    ratio = probs[0] / probs[1]
    assert abs(ratio - 2.0) < 1e-6
    assert abs(probs[0] - (2.0 / 3.0)) < 1e-6
    assert abs(probs[1] - (1.0 / 3.0)) < 1e-6


def test_feat_06_multiplicative_3way_standard(load_fixture: Callable[[str], Any]) -> None:
    """Verifies Multiplicative devig on standard 1X2 market against known fixture."""
    cases = {c["id"]: c for c in load_fixture("devig_cases.json")}
    case = cases["devig_3way_football_standard"]
    odds = case["odds"]

    probs = devig_multiplicative(odds)
    assert_devig_convergence(probs, odds, method="multiplicative", tolerance=1e-5)
    # 1/1.80 = 0.5556, 1/3.50 = 0.2857, 1/4.20 = 0.2381; sum = 1.0794
    assert abs(probs[0] - 0.5147) < 1e-3
    assert abs(probs[1] - 0.2647) < 1e-3
    assert abs(probs[2] - 0.2206) < 1e-3


def test_feat_06_multiplicative_low_margin_sharp(load_fixture: Callable[[str], Any]) -> None:
    """Verifies Multiplicative devig on low-margin Pinnacle benchmark odds."""
    cases = {c["id"]: c for c in load_fixture("devig_cases.json")}
    case = cases["devig_low_margin_sharp"]
    odds = case["odds"]

    probs = devig_multiplicative(odds)
    assert_devig_convergence(probs, odds, method="multiplicative")
    assert abs(probs[0] - 0.50) < 1e-4
    assert abs(probs[1] - 0.50) < 1e-4


def test_feat_06_multiplicative_arbitrary_5_outcomes() -> None:
    """Verifies Multiplicative devig with 5 distinct outcomes maintains sum and strict ordering."""
    odds = [3.00, 4.00, 5.00, 6.00, 7.00]
    probs = devig_multiplicative(odds)

    assert_devig_convergence(probs, odds, method="multiplicative")
    assert len(probs) == 5
    for i in range(len(probs) - 1):
        assert probs[i] > probs[i + 1]

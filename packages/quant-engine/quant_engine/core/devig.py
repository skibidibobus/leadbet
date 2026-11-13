"""Bookmaker margin removal (devigging) algorithms.

Implements:
- Multiplicative (proportional) normalization baseline.
- Power method via Brent root-finding.
- Shin method using algebraically stable conjugate root-finding.
- Strict probability invariant: sum(P) == 1.0 within 1e-6 tolerance.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Literal, Optional, Sequence
import numpy as np

from quant_engine.core.solvers import find_root_brent


class NegativeVigError(ValueError):
    """Raised when negative vig / arbitrage odds are supplied without allow_negative_vig=True."""


@dataclass(frozen=True)
class DevigResult:
    """Structured result of devigging computation."""

    probabilities: list[float]
    overround: float
    method: str
    parameter: Optional[float] = None  # z for Shin, c for Power


def _validate_odds(odds: Sequence[float]) -> np.ndarray:
    """Validate decimal odds vector."""
    if len(odds) < 2:
        raise ValueError(f"Odds vector must contain at least 2 outcomes, got {len(odds)}")
    arr = np.asarray(odds, dtype=np.float64)
    if not np.all(np.isfinite(arr)):
        raise ValueError("Odds vector contains NaN or infinite values")
    if np.any(arr <= 1.0):
        raise ValueError(f"All decimal odds must be strictly greater than 1.0: {odds}")
    return arr


def devig_multiplicative(odds: Sequence[float]) -> list[float]:
    """Proportional normalization baseline.

    p_i = (1 / O_i) / sum(1 / O_j)
    """
    arr = _validate_odds(odds)
    r = 1.0 / arr
    sum_r = float(np.sum(r))
    if sum_r <= 0.0:
        raise ValueError("Sum of implied probabilities must be positive")
    probs = (r / sum_r).tolist()
    return probs


def devig_power(
    odds: Sequence[float],
    bracket: tuple[float, float] = (0.5, 2.0),
) -> tuple[list[float], float]:
    """Power method solving sum_i (1/odds_i)^c = 1 via Brent root-finder.

    Returns:
        (probabilities, c_parameter)
    """
    arr = _validate_odds(odds)
    r = 1.0 / arr
    sum_r = float(np.sum(r))

    if abs(sum_r - 1.0) <= 1e-6:
        probs = (r / sum_r).tolist()
        return probs, 1.0

    def obj(c: float) -> float:
        return float(np.sum(r**c) - 1.0)

    a, b = bracket
    fa, fb = obj(a), obj(b)
    # Dynamically expand bracket if needed
    if fa * fb > 0:
        if fa > 0:
            b = 10.0
            fb = obj(b)
        else:
            a = 0.01
            fa = obj(a)

    if fa * fb > 0:
        # Fallback to wider search
        a, b = 0.001, 20.0

    c_star = find_root_brent(obj, a, b)
    p_raw = r**c_star
    p_norm = p_raw / np.sum(p_raw)
    return p_norm.tolist(), float(c_star)


def devig_shin_detailed(
    odds: Sequence[float],
    allow_negative_vig: bool = False,
) -> DevigResult:
    """Shin method eliminating favorite-longshot bias using stable conjugate form.

    Returns detailed DevigResult with insider proportion z in [0, 1).
    """
    arr = _validate_odds(odds)
    r = 1.0 / arr
    sum_r = float(np.sum(r))
    overround = sum_r - 1.0

    # Zero vig / Fair market
    if abs(overround) <= 1e-6:
        probs = (r / sum_r).tolist()
        return DevigResult(probabilities=probs, overround=overround, method="shin", parameter=0.0)

    # Negative vig / Arbitrage market
    if overround < 0:
        if not allow_negative_vig:
            raise NegativeVigError(
                f"Negative vig detected (overround {overround:.6f} < 0): arbitrage market"
            )
        probs = (r / sum_r).tolist()
        return DevigResult(probabilities=probs, overround=overround, method="shin_fallback", parameter=0.0)

    # Stable conjugate formula:
    # A_i = (1 / odds_i)^2 / sum(1 / odds)
    # p_i(z) = 2 * A_i / (sqrt(z^2 + 4 * (1 - z) * A_i) + z)
    # Solves sum p_i(z) - 1.0 = 0 on z in [0.0, 1.0].
    A = (r**2) / sum_r

    def obj(z: float) -> float:
        disc = np.maximum(0.0, z**2 + 4.0 * (1.0 - z) * A)
        denom = np.sqrt(disc) + z
        p = (2.0 * A) / np.maximum(denom, 1e-15)
        return float(np.sum(p) - 1.0)

    # At z=0: p_i = sqrt(A_i) = r_i / sqrt(sum_r) -> sum(p) = sqrt(sum_r) > 1 -> obj(0) > 0
    # At z=1: p_i = A_i = r_i^2 / sum_r -> sum(p) = sum(r_i^2)/sum_r < max(r_i) < 1 -> obj(1) < 0
    z_star = find_root_brent(obj, 0.0, 1.0)

    disc_star = np.maximum(0.0, z_star**2 + 4.0 * (1.0 - z_star) * A)
    denom_star = np.sqrt(disc_star) + z_star
    p_star = (2.0 * A) / np.maximum(denom_star, 1e-15)
    p_norm = (p_star / np.sum(p_star)).tolist()

    return DevigResult(
        probabilities=p_norm,
        overround=overround,
        method="shin",
        parameter=float(z_star),
    )


def devig_shin(
    odds: Sequence[float],
    allow_negative_vig: bool = False,
) -> list[float]:
    """Shin method returning fair probabilities."""
    res = devig_shin_detailed(odds, allow_negative_vig=allow_negative_vig)
    return res.probabilities


def devig(
    odds: Sequence[float],
    method: Literal["shin", "power", "multiplicative"] = "shin",
    allow_negative_vig: bool = False,
) -> DevigResult:
    """Unified devigging facade for 2-way and 3-way sports betting markets."""
    arr = _validate_odds(odds)
    r = 1.0 / arr
    overround = float(np.sum(r) - 1.0)

    if method == "shin":
        return devig_shin_detailed(odds, allow_negative_vig=allow_negative_vig)
    elif method == "power":
        if overround < 0 and not allow_negative_vig:
            raise NegativeVigError(
                f"Negative vig detected (overround {overround:.6f} < 0): arbitrage market"
            )
        probs, c = devig_power(odds)
        return DevigResult(probabilities=probs, overround=overround, method="power", parameter=c)
    elif method == "multiplicative":
        probs = devig_multiplicative(odds)
        return DevigResult(probabilities=probs, overround=overround, method="multiplicative")
    else:
        raise ValueError(f"Unknown devigging method: {method}")

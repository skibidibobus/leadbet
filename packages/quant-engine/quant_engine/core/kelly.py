"""Fractional Kelly Criterion staking and Expected Value sizing.

Implements:
- Standard Quarter-Kelly (gamma = 0.25).
- Hard safety cap at 5% (0.05) of bankroll.
- Stake = 0.0 if EV <= 0.
- Support for Polish tax factors (0.88x statutory turnover tax and 10% PIT threshold factor).
"""
from __future__ import annotations


def calculate_kelly_fraction(
    odds: float,
    probability: float,
    gamma: float = 0.25,
    max_cap: float = 0.05,
) -> float:
    """Calculate Fractional Kelly fraction with safety rules.

    Args:
        odds: Decimal odds (> 1.0).
        probability: True winning probability in (0, 1).
        gamma: Kelly fraction multiplier (default 0.25 for Quarter-Kelly).
        max_cap: Maximum bankroll fraction allowed (default 0.05 = 5%).

    Returns:
        Recommended fraction of bankroll in [0.0, max_cap].
    """
    if odds <= 1.0 or probability <= 0.0 or probability >= 1.0:
        return 0.0

    b = odds - 1.0
    q = 1.0 - probability
    ev = b * probability - q

    if ev <= 0.0:
        return 0.0

    f_star = gamma * (ev / b)
    return float(min(max_cap, max(0.0, f_star)))


def calculate_kelly_fraction_pl(
    odds_gross: float,
    probability: float,
    tax_multiplier: float = 0.88,
    is_pit_taxed: bool = False,
    gamma: float = 0.25,
    max_cap: float = 0.05,
) -> float:
    """Calculate Quarter-Kelly fraction factoring Polish turnover tax and PIT.

    Args:
        odds_gross: Gross decimal odds of the ticket (> 1.0).
        probability: True winning probability.
        tax_multiplier: Turnover tax factor (0.88 statutory, 1.00 promotional).
        is_pit_taxed: Whether payout exceeds 2280 PLN triggering 10% PIT (0.90x).
        gamma: Kelly fraction multiplier.
        max_cap: Maximum bankroll fraction allowed.

    Returns:
        Recommended bankroll fraction taking Polish legal taxes into account.
    """
    if odds_gross <= 1.0 or probability <= 0.0 or probability >= 1.0:
        return 0.0

    pit_factor = 0.90 if is_pit_taxed else 1.00
    odds_net = odds_gross * tax_multiplier * pit_factor

    if odds_net <= 1.0:
        return 0.0

    return calculate_kelly_fraction(
        odds=odds_net,
        probability=probability,
        gamma=gamma,
        max_cap=max_cap,
    )


def calculate_kelly_stake(
    bankroll: float,
    odds: float,
    probability: float,
    gamma: float = 0.25,
    max_cap: float = 0.05,
) -> float:
    """Calculate monetary stake in currency units given total bankroll."""
    if bankroll <= 0.0:
        return 0.0
    f = calculate_kelly_fraction(odds, probability, gamma=gamma, max_cap=max_cap)
    return round(bankroll * f, 2)

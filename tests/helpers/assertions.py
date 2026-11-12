"""Mathematical and Architectural Invariant Assertion Helpers.

Provides strict tolerance checks for probability theory, Polish tax regulations,
Kelly bankroll management, anti-correlation guards, and 60-30-10 design system rules.
"""

from __future__ import annotations

import math
from typing import Any, Mapping, Sequence, Union


def assert_probability_distribution(
    probabilities: Union[Sequence[float], Mapping[str, float]],
    tolerance: float = 1e-5,
) -> None:
    """Verifies that each probability is within [0.0, 1.0] and the sum equals 1.0 +- tolerance."""
    if isinstance(probabilities, dict):
        values = list(probabilities.values())
    else:
        values = list(probabilities)

    assert len(values) > 0, "Probability distribution must not be empty"

    total = 0.0
    for p in values:
        assert isinstance(p, (int, float)), f"Probability value must be float, got {type(p)}"
        assert -tolerance <= p <= 1.0 + tolerance, f"Probability {p} outside [0.0, 1.0]"
        total += p

    assert (
        abs(total - 1.0) <= tolerance
    ), f"Sum of probabilities {total} does not equal 1.0 (diff: {abs(total - 1.0)} > {tolerance})"


def assert_devig_convergence(
    devigged_probs: Sequence[float],
    original_odds: Sequence[float],
    method: str = "shin",
    tolerance: float = 1e-5,
) -> None:
    """Verifies de-vigging solver convergence and order preservation."""
    assert len(devigged_probs) == len(original_odds), (
        f"Devigged probs length {len(devigged_probs)} != original odds {len(original_odds)}"
    )
    assert_probability_distribution(devigged_probs, tolerance=tolerance)

    # Check monotonicity: lower odds -> higher probability
    paired = sorted(zip(original_odds, devigged_probs), key=lambda x: x[0])
    for i in range(len(paired) - 1):
        odd_a, prob_a = paired[i]
        odd_b, prob_b = paired[i + 1]
        if odd_a < odd_b:
            assert (
                prob_a >= prob_b - tolerance
            ), f"Monotonicity violation: Odds {odd_a} < {odd_b} but prob {prob_a} < {prob_b}"


def assert_polish_turnover_tax(
    stake: float,
    gross_odds: float,
    calculated_net_odds: float,
    calculated_net_payout: float,
    is_promotional: bool = False,
    tolerance: float = 0.02,
) -> None:
    """Verifies compliance with Polish 12% turnover tax under Ustawa o grach hazardowych."""
    assert stake > 0, f"Stake must be positive, got {stake}"
    assert gross_odds >= 1.0, f"Gross odds must be >= 1.0, got {gross_odds}"

    tax_multiplier = 1.00 if is_promotional else 0.88
    expected_net_odds = gross_odds * tax_multiplier
    expected_net_payout = stake * expected_net_odds

    assert abs(calculated_net_odds - expected_net_odds) < 0.01, (
        f"Net odds discrepancy: calculated={calculated_net_odds}, expected={expected_net_odds}"
    )
    assert abs(calculated_net_payout - expected_net_payout) <= tolerance, (
        f"Net payout discrepancy: calculated={calculated_net_payout}, expected={expected_net_payout}"
    )


def assert_polish_pit_threshold(
    gross_payout: float,
    calculated_net_payout: float,
    pit_applies: bool,
    pit_deduction: float,
    tolerance: float = 0.02,
) -> None:
    """Verifies strict compliance with the 10% PIT threshold on winnings exceeding 2280.00 PLN."""
    if gross_payout <= 2280.00:
        assert not pit_applies, (
            f"PIT 10% applied incorrectly for payout {gross_payout} <= 2280.00 PLN"
        )
        assert abs(pit_deduction - 0.0) <= tolerance, (
            f"PIT deduction {pit_deduction} != 0.0 for payout {gross_payout}"
        )
        assert abs(calculated_net_payout - gross_payout) <= tolerance, (
            f"Net payout {calculated_net_payout} != gross {gross_payout}"
        )
    else:
        assert pit_applies, (
            f"PIT 10% was NOT applied for payout {gross_payout} > 2280.00 PLN"
        )
        expected_deduction = round(0.10 * gross_payout, 2)
        expected_net = round(0.90 * gross_payout, 2)
        assert abs(pit_deduction - expected_deduction) <= tolerance, (
            f"PIT deduction discrepancy: calculated={pit_deduction}, expected={expected_deduction}"
        )
        assert abs(calculated_net_payout - expected_net) <= tolerance, (
            f"Net payout discrepancy after 10% PIT: calculated={calculated_net_payout}, expected={expected_net}"
        )


def assert_ticket_splitting_advice(
    stake: float,
    gross_payout: float,
    split_advice: Any,
) -> None:
    """Verifies coupon splitting advice when payout exceeds 2280 PLN."""
    def _get_val(obj: Any, key: str, default: Any = None) -> Any:
        if isinstance(obj, dict):
            return obj.get(key, default)
        return getattr(obj, key, default)

    if gross_payout > 2280.00 and (gross_payout / 2.0) <= 2280.00:
        assert split_advice is not None, f"Split advice expected for gross payout {gross_payout}"
        split_into = _get_val(split_advice, "split_into")
        stake_per_ticket = _get_val(split_advice, "stake_per_ticket", 0)
        tax_saved = _get_val(split_advice, "tax_saved", 0)
        assert split_into == 2, f"Expected 2-way split, got {split_into}"
        assert abs(stake_per_ticket - (stake / 2.0)) <= 0.01, (
            f"Split stake discrepancy: {stake_per_ticket} vs {stake / 2.0}"
        )
        assert abs(tax_saved - (0.10 * gross_payout)) <= 0.02, (
            f"Tax saved discrepancy: {tax_saved} vs {0.10 * gross_payout}"
        )
    elif gross_payout <= 2280.00:
        if split_advice is not None:
            tax_saved = _get_val(split_advice, "tax_saved", 0)
            assert tax_saved == 0.0, f"Expected zero tax saved for sub-threshold payout {gross_payout}"


def assert_anti_correlation_guard(selections: Sequence[Any]) -> None:
    """Verifies that no two legs in a generated coupon originate from the same match."""
    event_ids = []
    for sel in selections:
        if isinstance(sel, dict):
            event_ids.append(sel["event_id"])
        else:
            event_ids.append(getattr(sel, "event_id"))

    unique_ids = set(event_ids)
    assert len(event_ids) == len(unique_ids), (
        f"Anti-Correlation Guard violation! Duplicate event IDs detected in coupon: {event_ids}"
    )


def assert_fractional_kelly(
    fraction: float,
    expected_value: float,
    max_cap: float = 0.05,
) -> None:
    """Verifies Quarter-Kelly stake bounds: fraction in [0.0, 0.05], 0.0 if EV <= 0."""
    if expected_value <= 0.0:
        assert (
            fraction == 0.0
        ), f"Kelly fraction must be 0.0 for non-positive EV ({expected_value}), got {fraction}"
    else:
        assert (
            0.0 <= fraction <= max_cap + 1e-6
        ), f"Kelly fraction {fraction} exceeds safety cap {max_cap} or is negative"


def assert_never_color_alone(badge_label: str, ev_value: float) -> None:
    """Enforces WCAG 'Never Color Alone' rule: EV indicators must combine color with sign and arrow."""
    if ev_value > 0:
        assert "+" in badge_label, (
            f"Positive EV badge '{badge_label}' missing '+' sign"
        )
        assert (
            "▲" in badge_label or "↑" in badge_label
        ), f"Positive EV badge '{badge_label}' missing upward arrow ('▲')"
    elif ev_value < 0:
        assert "-" in badge_label, (
            f"Negative EV badge '{badge_label}' missing '-' sign"
        )
        assert (
            "▼" in badge_label or "↓" in badge_label
        ), f"Negative EV badge '{badge_label}' missing downward arrow ('▼')"


def calculate_relative_luminance(hex_code: str) -> float:
    """Calculates relative luminance according to WCAG 2.2."""
    h = hex_code.lstrip("#")
    r, g, b = tuple(int(h[i : i + 2], 16) for i in (0, 2, 4))

    def _chan(c: int) -> float:
        s = c / 255.0
        return s / 12.92 if s <= 0.04045 else ((s + 0.055) / 1.055) ** 2.4

    return 0.2126 * _chan(r) + 0.7152 * _chan(g) + 0.0722 * _chan(b)


def assert_wcag_contrast(
    foreground_hex: str,
    background_hex: str,
    min_ratio: float = 4.5,
) -> None:
    """Verifies WCAG contrast ratio (L1 + 0.05) / (L2 + 0.05) >= min_ratio."""
    l1 = calculate_relative_luminance(foreground_hex)
    l2 = calculate_relative_luminance(background_hex)
    ratio = (max(l1, l2) + 0.05) / (min(l1, l2) + 0.05)
    assert (
        ratio >= min_ratio
    ), f"WCAG contrast violation: {foreground_hex} on {background_hex} ratio {ratio:.2f} < {min_ratio}"

"""Focused unit tests for PolishTaxEngine using tests/fixtures/tax_cases.json."""
from __future__ import annotations

import json
import math
from pathlib import Path
import pytest

from bookmaker_adapters.tax.polish_tax import BookmakerMode, PolishTaxEngine

FIXTURES_PATH = Path(__file__).resolve().parents[3] / "tests" / "fixtures" / "tax_cases.json"


def _resolve_mode_and_legs(case: dict) -> tuple[BookmakerMode, list[float]]:
    cid = case["id"]
    if "legs" in case:
        legs = [float(leg["odds"]) for leg in case["legs"]]
        if "betclic" in cid:
            return BookmakerMode.BETCLIC_TAX_FREE, legs
        if "fortuna" in cid:
            return BookmakerMode.FORTUNA_PROMO, legs
        return BookmakerMode.STANDARD_088, legs

    gross = float(case["gross_odds"])
    if case.get("is_promotional"):
        # Promotional 1.00x requires >= 2 legs >= 1.20 under Betclic
        half = math.sqrt(gross)
        return BookmakerMode.BETCLIC_TAX_FREE, [half, half]
    return BookmakerMode.STANDARD_088, [gross]


def test_tax_cases_fixtures():
    cases = json.loads(FIXTURES_PATH.read_text(encoding="utf-8"))
    for case in cases:
        mode, leg_odds = _resolve_mode_and_legs(case)
        res = PolishTaxEngine.calculate_slip_tax(
            stake=float(case["stake"]),
            leg_odds=leg_odds,
            bookmaker_mode=mode,
        )
        if "expected_tax_multiplier" in case:
            assert res.tax_multiplier == pytest.approx(case["expected_tax_multiplier"], abs=1e-4), case["id"]
        if "pit_10_applies" in case:
            assert res.pit_10_applies is case["pit_10_applies"], case["id"]
        if "expected_net_odds" in case:
            assert res.net_odds == pytest.approx(case["expected_net_odds"], abs=0.05), case["id"]
        if "expected_net_payout" in case:
            assert res.potential_payout_net == pytest.approx(case["expected_net_payout"], abs=0.05), case["id"]
        if "pit_10_deduction" in case:
            assert res.pit_10_deduction == pytest.approx(case["pit_10_deduction"], abs=0.05), case["id"]
        if "split_into" in case:
            assert res.tax_savings_advice is not None
            assert res.tax_savings_advice.recommended is True
            assert res.tax_savings_advice.split_tickets_count == case["split_into"]
            assert res.tax_savings_advice.net_tax_saved == pytest.approx(case["tax_saved"], abs=0.05)


def test_split_advice_when_pit_exceeds_threshold():
    res = PolishTaxEngine.calculate_slip_tax(
        stake=1000.0,
        leg_odds=[2.0, 2.0],
        bookmaker_mode=BookmakerMode.BETCLIC_TAX_FREE,
    )
    assert res.pit_10_applies is True
    assert res.pit_10_deduction == pytest.approx(400.0, abs=0.01)
    assert res.tax_savings_advice is not None
    assert res.tax_savings_advice.recommended is True
    assert res.tax_savings_advice.split_tickets_count >= 2
    assert res.tax_savings_advice.payout_per_ticket <= 2280.0

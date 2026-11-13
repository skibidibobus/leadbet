"""Polish legal bookmaker tax engine (12% turnover tax, promos, 10% PIT > 2280 PLN)."""
from __future__ import annotations

import math
from enum import Enum
from typing import List, Optional, Union
from pydantic import BaseModel, Field


PIT_THRESHOLD_PLN = 2280.00
STANDARD_TAX_MULTIPLIER = 0.88
PIT_RATE = 0.10


class BookmakerMode(str, Enum):
    """Supported Polish legal bookmaker tax/promo modes."""

    STANDARD_088 = "standard_088"
    BETCLIC_TAX_FREE = "betclic_tax_free"
    FORTUNA_PROMO = "fortuna_promo"
    SUPERBET_BOOST = "superbet_boost"


class SplitAdvice(BaseModel):
    """Advice on splitting a slip to legally avoid the 10% PIT threshold (>2280 PLN)."""

    recommended: bool
    original_gross_payout: float
    original_tax_deduction: float
    split_tickets_count: int
    stake_per_ticket: float
    payout_per_ticket: float
    net_tax_saved: float
    advice_text: str


class TaxCalculationResult(BaseModel):
    """Full tax & payout calculation for a Polish legal bookmaker slip."""

    gross_odds: float
    tax_multiplier: float
    net_odds: float
    stake: float
    effective_stake: float
    potential_payout_gross: float
    potential_payout_net: float
    pit_10_applies: bool
    pit_10_deduction: float
    pit_warning: Optional[str] = None
    tax_savings_advice: Optional[SplitAdvice] = None


class PolishTaxEngine:
    """Calculates statutory Polish betting taxes and promotional zero-tax eligibility."""

    @staticmethod
    def resolve_tax_multiplier(
        bookmaker_mode: Union[BookmakerMode, str],
        leg_odds: List[float],
    ) -> float:
        """Determine the turnover tax multiplier (0.88 or 1.00) based on bookmaker rules."""
        mode = BookmakerMode(bookmaker_mode)
        if mode == BookmakerMode.STANDARD_088:
            return STANDARD_TAX_MULTIPLIER

        if mode == BookmakerMode.BETCLIC_TAX_FREE:
            # Betclic "Bez Podatku 2.0": >= 2 legs, each >= 1.20 odds
            if len(leg_odds) >= 2 and all(o >= 1.20 - 1e-9 for o in leg_odds):
                return 1.00
            return STANDARD_TAX_MULTIPLIER

        if mode == BookmakerMode.FORTUNA_PROMO:
            # Fortuna AKO promo: >= 3 legs, each >= 1.30 odds
            if len(leg_odds) >= 3 and all(o >= 1.30 - 1e-9 for o in leg_odds):
                return 1.00
            return STANDARD_TAX_MULTIPLIER

        if mode == BookmakerMode.SUPERBET_BOOST:
            # Superbet promo threshold: >= 3 legs, each >= 1.25 odds
            if len(leg_odds) >= 3 and all(o >= 1.25 - 1e-9 for o in leg_odds):
                return 1.00
            return STANDARD_TAX_MULTIPLIER

        return STANDARD_TAX_MULTIPLIER

    @classmethod
    def calculate_slip_tax(
        cls,
        stake: float,
        leg_odds: List[float],
        bookmaker_mode: Union[BookmakerMode, str] = BookmakerMode.STANDARD_088,
        gross_odds_override: Optional[float] = None,
    ) -> TaxCalculationResult:
        """Compute turnover tax, net odds, potential payout, 10% PIT (>2280 PLN) and split advice."""
        if stake < 1.0:
            raise ValueError("Stake must be at least 1.00 PLN.")
        if not leg_odds and gross_odds_override is None:
            raise ValueError("At least one leg odd or gross_odds_override is required.")

        gross_odds = (
            float(gross_odds_override)
            if gross_odds_override is not None
            else math.prod(leg_odds)
        )
        tax_multiplier = cls.resolve_tax_multiplier(bookmaker_mode, leg_odds)
        net_odds = gross_odds * tax_multiplier
        effective_stake = stake * tax_multiplier
        preliminary_payout = round(effective_stake * gross_odds, 2)

        pit_10_applies = preliminary_payout > PIT_THRESHOLD_PLN
        pit_10_deduction = round(preliminary_payout * PIT_RATE, 2) if pit_10_applies else 0.0
        potential_payout_net = round(preliminary_payout - pit_10_deduction, 2)

        pit_warning: Optional[str] = None
        split_advice: Optional[SplitAdvice] = None

        if pit_10_applies:
            pit_warning = (
                f"Wygrana wstępna ({preliminary_payout:.2f} PLN) przekracza próg 2280.00 PLN "
                f"— potrącono 10% PIT ({pit_10_deduction:.2f} PLN)."
            )
            split_count = int(math.ceil(preliminary_payout / PIT_THRESHOLD_PLN))
            # Avoid exact boundary equality floating issues by bumping if needed
            while split_count >= 2 and (preliminary_payout / split_count) > PIT_THRESHOLD_PLN:
                split_count += 1
            stake_per_ticket = round(stake / split_count, 2)
            if stake_per_ticket >= 1.0:
                payout_per_ticket = round(preliminary_payout / split_count, 2)
                split_advice = SplitAdvice(
                    recommended=True,
                    original_gross_payout=preliminary_payout,
                    original_tax_deduction=pit_10_deduction,
                    split_tickets_count=split_count,
                    stake_per_ticket=stake_per_ticket,
                    payout_per_ticket=payout_per_ticket,
                    net_tax_saved=pit_10_deduction,
                    advice_text=(
                        f"Wygrana przekracza 2280 PLN i podlega 10% PIT ({pit_10_deduction:.2f} PLN). "
                        f"Rozbij kupon na {split_count} identyczne zakłady po {stake_per_ticket:.2f} PLN "
                        f"(wygrana {payout_per_ticket:.2f} PLN każdy), aby legalnie zaoszczędzić {pit_10_deduction:.2f} PLN!"
                    ),
                )

        return TaxCalculationResult(
            gross_odds=round(gross_odds, 4),
            tax_multiplier=tax_multiplier,
            net_odds=round(net_odds, 4),
            stake=round(stake, 2),
            effective_stake=round(effective_stake, 2),
            potential_payout_gross=preliminary_payout,
            potential_payout_net=potential_payout_net,
            pit_10_applies=pit_10_applies,
            pit_10_deduction=pit_10_deduction,
            pit_warning=pit_warning,
            tax_savings_advice=split_advice,
        )

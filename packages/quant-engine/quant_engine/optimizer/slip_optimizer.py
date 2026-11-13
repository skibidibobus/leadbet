"""Combinatorial slip optimizer with Anti-Correlation Guard and Polish tax awareness."""
from __future__ import annotations

import math
import time
from typing import Dict, List, Optional, Tuple, Union
from pydantic import BaseModel, Field

from bookmaker_adapters.tax.polish_tax import BookmakerMode, PolishTaxEngine, SplitAdvice
from quant_engine.core.kelly import calculate_kelly_fraction


RISK_EV_WEIGHTS: Dict[str, float] = {
    "conservative": 0.05,
    "balanced": 0.20,
    "aggressive": 0.50,
    "max_value": 5.00,
}


class CandidateSelection(BaseModel):
    """Single candidate betting outcome eligible for slip construction."""

    event_id: str
    event_name: str
    sport: str
    league_name: str
    start_time_utc: str
    market_key: str
    market_label: str
    outcome_key: str
    outcome_label: str
    bookmaker_key: str
    odds_gross: float
    p_model: float
    p_sharp: float
    p_true: float
    ev_net: float = 0.0
    applied_tax_multiplier: float = 1.0


class SlipGenerateParams(BaseModel):
    """User personalization parameters for slip generation."""

    sports: List[str] = Field(default_factory=lambda: ["football", "basketball", "tennis", "hockey"])
    markets: Optional[List[str]] = None
    risk_profile: str = "balanced"
    target_odds_min: float = 2.50
    target_odds_max: float = 5.00
    min_legs: int = 2
    max_legs: int = 4
    min_leg_prob: float = 0.45
    stake: float = 100.0
    bookmaker_mode: Union[BookmakerMode, str] = BookmakerMode.BETCLIC_TAX_FREE
    only_plus_ev: bool = False
    custom_overrides: Dict[str, float] = Field(default_factory=dict)


class EvaluatedSlip(BaseModel):
    """Evaluated slip financial & probabilistic metrics."""

    selections: List[CandidateSelection]
    total_odds_gross: float
    tax_multiplier: float
    total_odds_net: float
    joint_probability: float
    stake: float
    potential_payout_gross: float
    potential_payout_net: float
    pit_10_applies: bool
    pit_10_deduction: float
    pit_warning: Optional[str] = None
    slip_ev_net: float
    kelly_stake_fraction: float
    kelly_recommended_stake_pln: float
    tax_savings_advice: Optional[SplitAdvice] = None
    is_correlated: bool = False
    anti_correlation_passed: bool = True
    validation_warnings: List[str] = Field(default_factory=list)


class GeneratedSlipProposal(EvaluatedSlip):
    """A ranked slip proposal returned by the optimizer."""

    id: str
    title: str
    risk_tier: str


class SlipOptimizer:
    """Beam-search combinatorial slip optimizer maximizing P(coupon) within target odds."""

    @staticmethod
    def evaluate_slip(
        selections: List[CandidateSelection],
        stake: float,
        bookmaker_mode: Union[BookmakerMode, str],
    ) -> EvaluatedSlip:
        """Evaluate joint probability, Polish taxes, net EV, Kelly fraction & correlation."""
        leg_odds = [s.odds_gross for s in selections]
        tax_res = PolishTaxEngine.calculate_slip_tax(
            stake=stake,
            leg_odds=leg_odds,
            bookmaker_mode=bookmaker_mode,
        )
        joint_prob = math.prod(s.p_true for s in selections) if selections else 0.0
        slip_ev_net = (
            (joint_prob * tax_res.potential_payout_net / stake) - 1.0
            if stake > 0 and selections
            else -1.0
        )
        effective_net_odds = (
            tax_res.potential_payout_net / stake if stake > 0 else tax_res.net_odds
        )
        kelly_frac = calculate_kelly_fraction(
            odds=max(effective_net_odds, 1.0001),
            probability=joint_prob,
            gamma=0.25,
            max_cap=0.05,
        )

        event_ids = [s.event_id for s in selections]
        is_correlated = len(event_ids) != len(set(event_ids))
        warnings: List[str] = []
        if is_correlated:
            warnings.append(
                "Uwaga: kupon zawiera więcej niż jedną selekcję z tego samego meczu (korelacja zdarzeń)."
            )
        if tax_res.tax_multiplier < 1.0 and str(bookmaker_mode) != BookmakerMode.STANDARD_088.value:
            warnings.append(
                "Kupon nie spełnia warunków promocji Bez Podatku — zastosowano ustawowy podatek 12% (0.88×)."
            )
        if slip_ev_net < 0:
            warnings.append(
                f"Ujemne EV netto ({slip_ev_net * 100:.1f}%) przy obecnym kursie i obciążeniu podatkowym."
            )

        updated_selections = [
            s.model_copy(
                update={
                    "applied_tax_multiplier": tax_res.tax_multiplier,
                    "ev_net": round(s.p_true * (s.odds_gross * tax_res.tax_multiplier) - 1.0, 4),
                }
            )
            for s in selections
        ]

        return EvaluatedSlip(
            selections=updated_selections,
            total_odds_gross=round(tax_res.gross_odds, 2),
            tax_multiplier=tax_res.tax_multiplier,
            total_odds_net=round(tax_res.net_odds, 2),
            joint_probability=round(joint_prob, 4),
            stake=round(stake, 2),
            potential_payout_gross=tax_res.potential_payout_gross,
            potential_payout_net=tax_res.potential_payout_net,
            pit_10_applies=tax_res.pit_10_applies,
            pit_10_deduction=tax_res.pit_10_deduction,
            pit_warning=tax_res.pit_warning,
            slip_ev_net=round(slip_ev_net, 4),
            kelly_stake_fraction=round(kelly_frac, 4),
            kelly_recommended_stake_pln=round(stake * kelly_frac, 2),
            tax_savings_advice=tax_res.tax_savings_advice,
            is_correlated=is_correlated,
            anti_correlation_passed=not is_correlated,
            validation_warnings=warnings,
        )

    @classmethod
    def generate_slips(
        cls,
        candidates: List[CandidateSelection],
        params: SlipGenerateParams,
        top_k: int = 3,
        beam_width: int = 48,
    ) -> Tuple[List[GeneratedSlipProposal], int, float]:
        """Search for top_k non-correlated slips maximizing P(coupon) within target odds."""
        t0 = time.perf_counter()

        # Apply user overrides if supplied
        normalized: List[CandidateSelection] = []
        for c in candidates:
            if c.sport not in params.sports:
                continue
            if params.markets and c.market_key not in params.markets:
                continue
            override_key = f"{c.event_id}:{c.market_key}:{c.outcome_key}"
            odds_val = params.custom_overrides.get(override_key, c.odds_gross)
            tax_mult = PolishTaxEngine.resolve_tax_multiplier(params.bookmaker_mode, [odds_val, odds_val])
            ev_val = c.p_true * (odds_val * tax_mult) - 1.0
            if c.p_true < params.min_leg_prob:
                continue
            if params.only_plus_ev and ev_val <= 0.0:
                continue
            normalized.append(
                c.model_copy(update={"odds_gross": round(odds_val, 3), "ev_net": round(ev_val, 4)})
            )

        # Keep best 1-2 selections per event sorted by p_true to avoid combinatorial explosion
        normalized.sort(key=lambda x: (x.p_true, x.ev_net), reverse=True)
        pool_size = len(normalized)
        if pool_size == 0:
            return [], 0, round((time.perf_counter() - t0) * 1000.0, 2)

        beta = RISK_EV_WEIGHTS.get(params.risk_profile, 0.20)
        beam: List[Tuple[float, List[CandidateSelection]]] = [(0.0, [])]
        in_range_solutions: List[Tuple[float, EvaluatedSlip]] = []
        fallback_solutions: List[Tuple[float, EvaluatedSlip]] = []
        seen_signatures = set()

        for depth in range(1, params.max_legs + 1):
            next_beam: List[Tuple[float, List[CandidateSelection]]] = []
            for _, current_legs in beam:
                used_events = {leg.event_id for leg in current_legs}
                last_idx = -1
                if current_legs:
                    last_id = current_legs[-1]
                    try:
                        last_idx = normalized.index(last_id)
                    except ValueError:
                        last_idx = -1

                for idx in range(last_idx + 1, pool_size):
                    cand = normalized[idx]
                    # Anti-Correlation Guard: max 1 leg per event
                    if cand.event_id in used_events:
                        continue
                    new_legs = current_legs + [cand]
                    gross = math.prod(l.odds_gross for l in new_legs)
                    if gross > params.target_odds_max * 1.25:
                        continue

                    p_joint = math.prod(l.p_true for l in new_legs)
                    score = math.log(max(p_joint, 1e-9)) + beta * sum(l.ev_net for l in new_legs)
                    next_beam.append((score, new_legs))

                    if depth >= params.min_legs:
                        sig = tuple(sorted(f"{l.event_id}:{l.market_key}:{l.outcome_key}" for l in new_legs))
                        if sig in seen_signatures:
                            continue
                        seen_signatures.add(sig)
                        evaluated = cls.evaluate_slip(new_legs, params.stake, params.bookmaker_mode)
                        obj_score = (
                            math.log(max(evaluated.joint_probability, 1e-9))
                            + beta * evaluated.slip_ev_net
                        )
                        if params.target_odds_min <= evaluated.total_odds_gross <= params.target_odds_max:
                            in_range_solutions.append((obj_score, evaluated))
                        else:
                            # Penalize distance from target odds bracket for fallback
                            dist = min(
                                abs(evaluated.total_odds_gross - params.target_odds_min),
                                abs(evaluated.total_odds_gross - params.target_odds_max),
                            )
                            fallback_solutions.append((obj_score - dist * 0.8, evaluated))

            next_beam.sort(key=lambda item: item[0], reverse=True)
            beam = next_beam[:beam_width]
            if not beam:
                break

        ranked = sorted(in_range_solutions, key=lambda x: x[0], reverse=True)
        if not ranked:
            ranked = sorted(fallback_solutions, key=lambda x: x[0], reverse=True)

        proposals: List[GeneratedSlipProposal] = []
        titles = [
            "Optymalny Kupon AKO (Najwyższa Szansa)",
            "Alternatywny Kupon Zbalansowany",
            "Wariant Rozszerzony (+EV / Dywersyfikacja)",
        ]
        for idx, (_, ev_slip) in enumerate(ranked[:top_k]):
            proposals.append(
                GeneratedSlipProposal(
                    id=f"slip_opt_{idx + 1:02d}",
                    title=titles[idx] if idx < len(titles) else f"Propozycja #{idx + 1}",
                    risk_tier=params.risk_profile,
                    **ev_slip.model_dump(),
                )
            )

        elapsed_ms = round((time.perf_counter() - t0) * 1000.0, 2)
        return proposals, pool_size, elapsed_ms

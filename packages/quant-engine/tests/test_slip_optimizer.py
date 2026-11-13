"""Focused unit tests for SlipOptimizer and Anti-Correlation Guard."""
from __future__ import annotations

from quant_engine.optimizer.slip_optimizer import (
    CandidateSelection,
    SlipGenerateParams,
    SlipOptimizer,
)


def _sample_candidates() -> list[CandidateSelection]:
    return [
        # Two outcomes from the SAME event (evt_1) to test Anti-Correlation Guard
        CandidateSelection(
            event_id="evt_1",
            event_name="Arsenal vs Chelsea",
            sport="football",
            league_name="Premier League",
            start_time_utc="2026-11-14T15:00:00Z",
            market_key="1x2",
            market_label="1X2",
            outcome_key="home",
            outcome_label="Arsenal",
            bookmaker_key="betclic",
            odds_gross=1.80,
            p_model=0.58,
            p_sharp=0.56,
            p_true=0.57,
        ),
        CandidateSelection(
            event_id="evt_1",
            event_name="Arsenal vs Chelsea",
            sport="football",
            league_name="Premier League",
            start_time_utc="2026-11-14T15:00:00Z",
            market_key="totals",
            market_label="Over 2.5",
            outcome_key="over_2_5",
            outcome_label="Powyżej 2.5",
            bookmaker_key="betclic",
            odds_gross=1.90,
            p_model=0.56,
            p_sharp=0.55,
            p_true=0.555,
        ),
        CandidateSelection(
            event_id="evt_2",
            event_name="Lakers vs Celtics",
            sport="basketball",
            league_name="NBA",
            start_time_utc="2026-11-14T23:00:00Z",
            market_key="h2h",
            market_label="Zwycięzca",
            outcome_key="home",
            outcome_label="Lakers",
            bookmaker_key="betclic",
            odds_gross=1.75,
            p_model=0.60,
            p_sharp=0.59,
            p_true=0.595,
        ),
        CandidateSelection(
            event_id="evt_3",
            event_name="Świątek vs Sabalenka",
            sport="tennis",
            league_name="WTA",
            start_time_utc="2026-11-14T18:00:00Z",
            market_key="h2h",
            market_label="Zwycięzca",
            outcome_key="home",
            outcome_label="Świątek",
            bookmaker_key="betclic",
            odds_gross=1.60,
            p_model=0.65,
            p_sharp=0.64,
            p_true=0.645,
        ),
    ]


def test_anti_correlation_guard_rejects_same_event():
    candidates = _sample_candidates()
    evaluated = SlipOptimizer.evaluate_slip(
        selections=[candidates[0], candidates[1]],
        stake=100.0,
        bookmaker_mode="betclic_tax_free",
    )
    assert evaluated.is_correlated is True
    assert evaluated.anti_correlation_passed is False
    assert evaluated.validation_warnings


def test_generate_slips_respects_target_odds_and_correlation():
    candidates = _sample_candidates()
    params = SlipGenerateParams(
        sports=["football", "basketball", "tennis"],
        target_odds_min=2.50,
        target_odds_max=5.50,
        min_legs=2,
        max_legs=3,
        stake=100.0,
        bookmaker_mode="betclic_tax_free",
    )
    proposals, pool_size, _ = SlipOptimizer.generate_slips(candidates, params, top_k=3)
    assert pool_size == 4
    assert len(proposals) >= 1
    for p in proposals:
        assert p.anti_correlation_passed is True
        event_ids = [s.event_id for s in p.selections]
        assert len(event_ids) == len(set(event_ids))
        assert params.target_odds_min <= p.total_odds_gross <= params.target_odds_max

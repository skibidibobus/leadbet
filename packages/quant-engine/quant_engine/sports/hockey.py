"""Ice Hockey Skellam goal difference model with stochastic empty net adjustment."""
from __future__ import annotations

import math
from typing import Any, Dict, List, Optional
import numpy as np

try:
    from scipy.special import iv as scipy_iv
    _HAS_SCIPY = True
except ImportError:
    _HAS_SCIPY = False

from quant_engine.sports.base import (
    CompetitorInput,
    MarketPrediction,
    MatchContext,
    SportPredictionResult,
)


def bessel_iv(v: float, z: float) -> float:
    """Modified Bessel function of the first kind I_v(z)."""
    if _HAS_SCIPY:
        try:
            return float(scipy_iv(v, z))
        except Exception:
            pass
    # Pure Python Taylor series expansion fallback:
    # I_v(z) = sum_{m=0}^\infty (1 / (m! * Gamma(m + v + 1))) * (z / 2)^(2m + v)
    abs_v = int(abs(v))
    half_z = z / 2.0
    term = (half_z**abs_v) / math.factorial(abs_v)
    total = term
    for m in range(1, 60):
        term = term * (half_z**2) / (m * (m + abs_v))
        total += term
        if term < 1e-15 * total:
            break
    return float(total)


def skellam_pmf(k: int, lambda_h: float, mu_a: float) -> float:
    """Skellam probability mass function for difference of two Poisson variables."""
    if lambda_h <= 0.0 and mu_a <= 0.0:
        return 1.0 if k == 0 else 0.0
    if lambda_h <= 0.0:
        # Purely away Poisson
        return float(math.exp(-mu_a) * (mu_a**(-k)) / math.factorial(-k)) if k <= 0 else 0.0
    if mu_a <= 0.0:
        # Purely home Poisson
        return float(math.exp(-lambda_h) * (lambda_h**k) / math.factorial(k)) if k >= 0 else 0.0

    z = 2.0 * math.sqrt(lambda_h * mu_a)
    scale = (lambda_h / mu_a) ** (k / 2.0)
    bessel = bessel_iv(abs(k), z)
    return float(math.exp(-(lambda_h + mu_a)) * scale * bessel)


class HockeyModel:
    """Ice Hockey Skellam model (60' regulation) with late-game empty net adjustment."""

    MODEL_VERSION = "hockey_skellam_emptynet_v1"
    DEFAULT_LEAGUE_GOALS = 3.0
    DEFAULT_EMPTY_NET_WINDOW = 2.0  # Final 2 minutes
    DEFAULT_EMPTY_NET_MULTIPLIER = 1.35

    @classmethod
    def calculate_intensities(
        cls,
        home: CompetitorInput,
        away: CompetitorInput,
        league_avg_goals: float = DEFAULT_LEAGUE_GOALS,
    ) -> tuple[float, float]:
        """Compute regulation 60-min goal scoring intensities lambda_h and mu_a."""
        h_att = home.goals_attack if home.goals_attack is not None else league_avg_goals
        h_def = home.goals_defense if home.goals_defense is not None else league_avg_goals
        a_att = away.goals_attack if away.goals_attack is not None else league_avg_goals
        a_def = away.goals_defense if away.goals_defense is not None else league_avg_goals

        # Home ice advantage ~ 1.10
        lambda_h = (h_att * a_def / max(league_avg_goals, 1.0)) * 1.10
        mu_a = (a_att * h_def / max(league_avg_goals, 1.0))

        return max(0.5, float(lambda_h)), max(0.5, float(mu_a))

    @classmethod
    def generate_goal_difference_distribution(
        cls,
        lambda_h: float,
        mu_a: float,
        max_diff: int = 10,
    ) -> tuple[dict[int, float], dict[int, float]]:
        """Compute raw Skellam and empty-net adjusted goal difference distributions."""
        p_raw: dict[int, float] = {}
        for k in range(-max_diff, max_diff + 1):
            p_raw[k] = skellam_pmf(k, lambda_h, mu_a)

        # Normalize raw distribution
        sum_raw = sum(p_raw.values())
        if sum_raw > 0:
            for k in p_raw:
                p_raw[k] /= sum_raw

        # Late-Game Empty Net Transition Matrix:
        # Trailing by 1 goal (k = 1 or -1):
        # - Equalize (k -> 0): 12%
        # - Empty net goal (k -> 2 or -2): 32%
        # - Stand pat (no score): 56%
        # Trailing by 2 goals (k = 2 or -2):
        # - Cut deficit (k -> 1 or -1): 8%
        # - Empty net goal (k -> 3 or -3): 22%
        # - Stand pat: 70%
        p_adj: dict[int, float] = dict(p_raw)

        p0_1 = p_raw.get(1, 0.0)
        p0_m1 = p_raw.get(-1, 0.0)
        p0_2 = p_raw.get(2, 0.0)
        p0_m2 = p_raw.get(-2, 0.0)

        # Transition formulas
        p_adj[0] = p_raw.get(0, 0.0) + 0.12 * p0_1 + 0.12 * p0_m1
        p_adj[1] = 0.56 * p0_1 + 0.08 * p0_2
        p_adj[-1] = 0.56 * p0_m1 + 0.08 * p0_m2
        p_adj[2] = 0.70 * p0_2 + 0.32 * p0_1
        p_adj[-2] = 0.70 * p0_m2 + 0.32 * p0_m1
        p_adj[3] = p_raw.get(3, 0.0) + 0.22 * p0_2
        p_adj[-3] = p_raw.get(-3, 0.0) + 0.22 * p0_m2

        # Normalize adjusted
        sum_adj = sum(p_adj.values())
        if sum_adj > 0:
            for k in p_adj:
                p_adj[k] /= sum_adj

        return p_raw, p_adj

    @classmethod
    def predict(cls, ctx: MatchContext) -> SportPredictionResult:
        """Execute Ice Hockey Skellam + empty net simulation."""
        lambda_h, mu_a = cls.calculate_intensities(
            home=ctx.home_competitor,
            away=ctx.away_competitor,
            league_avg_goals=ctx.league_avg_goals,
        )

        p_raw, p_adj = cls.generate_goal_difference_distribution(lambda_h, mu_a, max_diff=10)

        # Regulation 1X2 market
        p_home_reg = sum(p_adj[k] for k in p_adj if k > 0)
        p_draw_reg = p_adj[0]
        p_away_reg = sum(p_adj[k] for k in p_adj if k < 0)

        # Moneyline (including Overtime & Shootout)
        # In OT/SO, home win probability based on intensity share
        p_ot_home = lambda_h / (lambda_h + mu_a)
        p_ml_home = p_home_reg + p_draw_reg * p_ot_home
        p_ml_away = max(0.0, 1.0 - p_ml_home)

        # Puck Line (-1.5 / +1.5)
        p_puckline_home_minus15 = sum(p_adj[k] for k in p_adj if k >= 2)
        p_puckline_away_plus15 = max(0.0, 1.0 - p_puckline_home_minus15)

        # Totals Over/Under (5.5, 6.5)
        # Expected total regulation goals + late-game empty net shift (+0.35 goals)
        expected_total = lambda_h + mu_a + 0.35
        # Poisson sum over total goals
        markets: Dict[str, MarketPrediction] = {
            "regulation_1x2": MarketPrediction(
                market_key="regulation_1x2",
                market_label="Regulation Result (60 Min 1X2)",
                outcomes={
                    "home": round(p_home_reg, 5),
                    "draw": round(p_draw_reg, 5),
                    "away": round(p_away_reg, 5),
                },
            ),
            "moneyline": MarketPrediction(
                market_key="moneyline",
                market_label="Match Winner (Incl. OT & Shootout)",
                outcomes={"home": round(p_ml_home, 5), "away": round(p_ml_away, 5)},
            ),
            "puck_line": MarketPrediction(
                market_key="puck_line",
                market_label="Puck Line (-1.5 / +1.5)",
                outcomes={
                    "home": round(p_puckline_home_minus15, 5),
                    "away": round(p_puckline_away_plus15, 5),
                },
            ),
        }

        for total_line in [4.5, 5.5, 6.5, 7.5]:
            p_under = sum(
                math.exp(-expected_total) * (expected_total**g) / math.factorial(g)
                for g in range(int(total_line) + 1)
            )
            p_over = max(0.0, 1.0 - p_under)
            key = f"total_{str(total_line).replace('.', '_')}"
            markets[key] = MarketPrediction(
                market_key=key,
                market_label=f"Total Goals Over/Under {total_line}",
                outcomes={"over": round(p_over, 5), "under": round(p_under, 5)},
            )

        diff_dist_list = [
            {"goal_diff": k, "prob": round(float(p_adj[k]), 5)}
            for k in range(-5, 6)
        ]

        breakdown = {
            "lambda_home": round(lambda_h, 3),
            "mu_away": round(mu_a, 3),
            "empty_net_multiplier": cls.DEFAULT_EMPTY_NET_MULTIPLIER,
            "empty_net_time_window_min": cls.DEFAULT_EMPTY_NET_WINDOW,
            "regulation_draw_prob": round(p_draw_reg, 4),
            "skellam_diff_distribution": diff_dist_list,
        }

        return SportPredictionResult(
            event_id=ctx.event_id,
            sport="hockey",
            model_version=cls.MODEL_VERSION,
            markets=markets,
            breakdown=breakdown,
        )

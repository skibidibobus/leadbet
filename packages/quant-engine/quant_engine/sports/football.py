"""Football Dixon-Coles Bivariate Poisson model with xG blending and tau low-score adjustment."""
from __future__ import annotations

import math
from typing import Any, Dict, List, Optional
import numpy as np

from quant_engine.sports.base import (
    CompetitorInput,
    MarketPrediction,
    MatchContext,
    SportPredictionResult,
)


def compute_tau(x: int, y: int, lambda_h: float, mu_a: float, rho: float) -> float:
    """Dixon-Coles tau adjustment factor for low-scoring match outcomes."""
    if x == 0 and y == 0:
        return 1.0 - lambda_h * mu_a * rho
    elif x == 0 and y == 1:
        return 1.0 + lambda_h * rho
    elif x == 1 and y == 0:
        return 1.0 + mu_a * rho
    elif x == 1 and y == 1:
        return 1.0 - rho
    return 1.0


def poisson_pmf(k: int, lmbda: float) -> float:
    """Poisson probability mass function P(X = k; lmbda)."""
    if lmbda <= 0.0:
        return 1.0 if k == 0 else 0.0
    return math.exp(-lmbda) * (lmbda**k) / math.factorial(k)


class FootballModel:
    """Dixon-Coles bivariate Poisson model with 70% xG / 30% goal weighting."""

    MODEL_VERSION = "dixon_coles_xg_v1"
    DEFAULT_RHO = -0.11
    DEFAULT_HOME_ADVANTAGE = 1.22
    XG_WEIGHT = 0.70
    GOALS_WEIGHT = 0.30

    @classmethod
    def calculate_intensities(
        cls,
        home: CompetitorInput,
        away: CompetitorInput,
        league_avg_xg: float = 1.35,
        league_avg_goals: float = 1.40,
        home_advantage: float = DEFAULT_HOME_ADVANTAGE,
    ) -> tuple[float, float, float, float]:
        """Calculate expected scoring intensities lambda_home and mu_away."""
        # Defaults if stats missing
        h_xg_att = home.xg_attack if home.xg_attack is not None else league_avg_xg
        h_xg_def = home.xg_defense if home.xg_defense is not None else league_avg_xg
        a_xg_att = away.xg_attack if away.xg_attack is not None else league_avg_xg
        a_xg_def = away.xg_defense if away.xg_defense is not None else league_avg_xg

        h_g_att = home.goals_attack if home.goals_attack is not None else h_xg_att
        h_g_def = home.goals_defense if home.goals_defense is not None else h_xg_def
        a_g_att = away.goals_attack if away.goals_attack is not None else a_xg_att
        a_g_def = away.goals_defense if away.goals_defense is not None else a_xg_def

        # xG intensities
        lambda_xg = (h_xg_att * a_xg_def / max(league_avg_xg, 0.1)) * home_advantage
        mu_xg = (a_xg_att * h_xg_def / max(league_avg_xg, 0.1))

        # Goals intensities
        lambda_goals = (h_g_att * a_g_def / max(league_avg_goals, 0.1)) * home_advantage
        mu_goals = (a_g_att * h_g_def / max(league_avg_goals, 0.1))

        # Blended intensities (70% xG / 30% actual goals)
        lambda_h = cls.XG_WEIGHT * lambda_xg + cls.GOALS_WEIGHT * lambda_goals
        mu_a = cls.XG_WEIGHT * mu_xg + cls.GOALS_WEIGHT * mu_goals

        lambda_h = max(0.05, float(lambda_h))
        mu_a = max(0.05, float(mu_a))

        return lambda_h, mu_a, float(lambda_xg), float(mu_xg)

    @classmethod
    def generate_score_matrix(
        cls,
        lambda_h: float,
        mu_a: float,
        rho: float = DEFAULT_RHO,
        max_goals: int = 8,
    ) -> tuple[np.ndarray, float]:
        """Generate normalized exact score matrix (max_goals x max_goals)."""
        # Clamp rho to maintain valid bivariate probabilities
        rho_min = max(-1.0 / max(lambda_h, 1e-4), -1.0 / max(mu_a, 1e-4))
        rho_max = min(1.0, 1.0 / (max(lambda_h, 1e-4) * max(mu_a, 1e-4)))
        clamped_rho = float(np.clip(rho, rho_min + 1e-4, rho_max - 1e-4))

        matrix = np.zeros((max_goals, max_goals), dtype=np.float64)
        for x in range(max_goals):
            px = poisson_pmf(x, lambda_h)
            for y in range(max_goals):
                py = poisson_pmf(y, mu_a)
                tau = compute_tau(x, y, lambda_h, mu_a, clamped_rho)
                matrix[x, y] = max(0.0, tau * px * py)

        total_sum = float(np.sum(matrix))
        if total_sum > 0:
            matrix = matrix / total_sum
        return matrix, clamped_rho

    @classmethod
    def predict(cls, ctx: MatchContext) -> SportPredictionResult:
        """Execute Dixon-Coles prediction pipeline."""
        home_adv = ctx.explicit_params.get("home_advantage", cls.DEFAULT_HOME_ADVANTAGE)
        rho_param = ctx.explicit_params.get("rho", cls.DEFAULT_RHO)

        lambda_h, mu_a, lambda_xg, mu_xg = cls.calculate_intensities(
            home=ctx.home_competitor,
            away=ctx.away_competitor,
            league_avg_xg=ctx.league_avg_xg,
            league_avg_goals=ctx.league_avg_goals,
            home_advantage=home_adv,
        )

        matrix, effective_rho = cls.generate_score_matrix(
            lambda_h=lambda_h,
            mu_a=mu_a,
            rho=rho_param,
            max_goals=8,
        )

        # 1X2 market
        p_home = float(np.sum(np.tril(matrix, -1)))
        p_draw = float(np.sum(np.diag(matrix)))
        p_away = float(np.sum(np.triu(matrix, 1)))

        markets: Dict[str, MarketPrediction] = {
            "1x2": MarketPrediction(
                market_key="1x2",
                market_label="Match Result (1X2)",
                outcomes={
                    "home": round(p_home, 5),
                    "draw": round(p_draw, 5),
                    "away": round(p_away, 5),
                },
            )
        }

        # Totals Over/Under 0.5, 1.5, 2.5, 3.5, 4.5
        for line in [0.5, 1.5, 2.5, 3.5, 4.5]:
            p_over = 0.0
            for x in range(8):
                for y in range(8):
                    if (x + y) > line:
                        p_over += float(matrix[x, y])
            p_under = max(0.0, 1.0 - p_over)
            key = f"total_{str(line).replace('.', '_')}"
            markets[key] = MarketPrediction(
                market_key=key,
                market_label=f"Total Goals Over/Under {line}",
                outcomes={"over": round(p_over, 5), "under": round(p_under, 5)},
            )

        # Both Teams to Score (BTTS)
        p_btts_yes = float(np.sum(matrix[1:, 1:]))
        p_btts_no = max(0.0, 1.0 - p_btts_yes)
        markets["btts"] = MarketPrediction(
            market_key="btts",
            market_label="Both Teams to Score",
            outcomes={"yes": round(p_btts_yes, 5), "no": round(p_btts_no, 5)},
        )

        # Asian Handicap / DNB lines
        # DNB (Asian 0.0)
        p_dnb_home = p_home / (p_home + p_away) if (p_home + p_away) > 0 else 0.5
        p_dnb_away = p_away / (p_home + p_away) if (p_home + p_away) > 0 else 0.5
        markets["dnb"] = MarketPrediction(
            market_key="dnb",
            market_label="Draw No Bet (Asian 0)",
            outcomes={"home": round(p_dnb_home, 5), "away": round(p_dnb_away, 5)},
        )

        # Asian Handicap -1.5 / +1.5
        p_ah_h_minus15 = 0.0
        for x in range(8):
            for y in range(8):
                if (x - y) >= 2:
                    p_ah_h_minus15 += float(matrix[x, y])
        p_ah_a_plus15 = max(0.0, 1.0 - p_ah_h_minus15)
        markets["asian_handicap_minus_1_5"] = MarketPrediction(
            market_key="asian_handicap_minus_1_5",
            market_label="Asian Handicap (-1.5 / +1.5)",
            outcomes={"home": round(p_ah_h_minus15, 5), "away": round(p_ah_a_plus15, 5)},
        )

        # Extract top 5 most likely scores
        score_probs = []
        for x in range(8):
            for y in range(8):
                score_probs.append({"score": f"{x}:{y}", "prob": round(float(matrix[x, y]), 5)})
        score_probs.sort(key=lambda item: item["prob"], reverse=True)
        most_likely_scores = score_probs[:5]

        matrix_list = [[round(float(matrix[x, y]), 6) for y in range(8)] for x in range(8)]

        breakdown = {
            "lambda_home": round(lambda_h, 4),
            "mu_away": round(mu_a, 4),
            "rho_correlation": round(effective_rho, 4),
            "xg_weight": cls.XG_WEIGHT,
            "goals_weight": cls.GOALS_WEIGHT,
            "xg_home_adjusted": round(lambda_xg, 4),
            "xg_away_adjusted": round(mu_xg, 4),
            "home_advantage": round(home_adv, 2),
            "score_matrix_8x8": matrix_list,
            "most_likely_scores": most_likely_scores,
        }

        return SportPredictionResult(
            event_id=ctx.event_id,
            sport="football",
            model_version=cls.MODEL_VERSION,
            markets=markets,
            breakdown=breakdown,
        )

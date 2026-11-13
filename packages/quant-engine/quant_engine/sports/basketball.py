"""Basketball possession pace model with Gaussian point spread and total points distributions."""
from __future__ import annotations

import math
from typing import Any, Dict, Optional
import numpy as np

from quant_engine.sports.base import (
    CompetitorInput,
    MarketPrediction,
    MatchContext,
    SportPredictionResult,
)


def normal_cdf(x: float, mu: float = 0.0, sigma: float = 1.0) -> float:
    """Standard normal cumulative distribution function Phi((x - mu) / sigma)."""
    if sigma <= 0.0:
        return 1.0 if x >= mu else 0.0
    z = (x - mu) / (sigma * math.sqrt(2.0))
    return float(0.5 * (1.0 + math.erf(z)))


class BasketballModel:
    """Possession-based pace model with ORtg/DRtg ratings and normal distribution spreads."""

    MODEL_VERSION = "basketball_pace_gaussian_v1"
    DEFAULT_LEAGUE_PACE = 100.0
    DEFAULT_LEAGUE_RTG = 112.0
    DEFAULT_HCA_POINTS = 2.8
    DEFAULT_FATIGUE_PENALTY = 2.5
    DEFAULT_SIGMA_DIFF = 11.8
    DEFAULT_SIGMA_TOT = 17.5

    @classmethod
    def calculate_expected_points(
        cls,
        home: CompetitorInput,
        away: CompetitorInput,
        league_avg_pace: float = DEFAULT_LEAGUE_PACE,
        league_avg_rtg: float = DEFAULT_LEAGUE_RTG,
        hca_pts: float = DEFAULT_HCA_POINTS,
        fatigue_penalty: float = DEFAULT_FATIGUE_PENALTY,
    ) -> tuple[float, float, float, float, float, float, float, float]:
        """Compute match pace and expected points for home and away teams."""
        pace_h = home.pace if home.pace is not None else league_avg_pace
        pace_a = away.pace if away.pace is not None else league_avg_pace
        expected_pace = (pace_h * pace_a) / max(league_avg_pace, 50.0)

        ortg_h = home.ortg if home.ortg is not None else league_avg_rtg
        drtg_h = home.drtg if home.drtg is not None else league_avg_rtg
        ortg_a = away.ortg if away.ortg is not None else league_avg_rtg
        drtg_a = away.drtg if away.drtg is not None else league_avg_rtg

        eff_h = ortg_h + drtg_a - league_avg_rtg
        eff_a = ortg_a + drtg_h - league_avg_rtg

        mu_h_base = (expected_pace / 100.0) * eff_h
        mu_a_base = (expected_pace / 100.0) * eff_a

        # Rest adjustments (0 rest days = back-to-back penalty)
        pen_h = fatigue_penalty if home.rest_days == 0 else 0.0
        pen_a = fatigue_penalty if away.rest_days == 0 else 0.0

        mu_h = mu_h_base + hca_pts - pen_h
        mu_a = mu_a_base - pen_a

        return expected_pace, mu_h, mu_a, ortg_h, drtg_h, ortg_a, drtg_a, hca_pts

    @classmethod
    def predict(cls, ctx: MatchContext) -> SportPredictionResult:
        """Execute Basketball pace and Gaussian spread simulation."""
        hca = ctx.explicit_params.get("hca_points", cls.DEFAULT_HCA_POINTS)
        fatigue = ctx.explicit_params.get("fatigue_penalty", cls.DEFAULT_FATIGUE_PENALTY)
        sigma_diff = ctx.explicit_params.get("sigma_diff", cls.DEFAULT_SIGMA_DIFF)
        sigma_tot = ctx.explicit_params.get("sigma_tot", cls.DEFAULT_SIGMA_TOT)

        exp_pace, mu_h, mu_a, ortg_h, drtg_h, ortg_a, drtg_a, hca_pts = cls.calculate_expected_points(
            home=ctx.home_competitor,
            away=ctx.away_competitor,
            league_avg_pace=ctx.league_avg_pace,
            league_avg_rtg=ctx.league_avg_rtg,
            hca_pts=hca,
            fatigue_penalty=fatigue,
        )

        mu_diff = mu_h - mu_a
        mu_tot = mu_h + mu_a

        # Moneyline: Home wins if score difference D > 0
        p_home_ml = normal_cdf(mu_diff / sigma_diff)
        p_away_ml = max(0.0, 1.0 - p_home_ml)

        markets: Dict[str, MarketPrediction] = {
            "moneyline": MarketPrediction(
                market_key="moneyline",
                market_label="Match Winner (Moneyline)",
                outcomes={"home": round(p_home_ml, 5), "away": round(p_away_ml, 5)},
            )
        }

        # Point Spreads (-9.5 to +9.5 in 2.0 increments)
        for spread in [-7.5, -5.5, -4.5, -3.5, -1.5, 1.5, 3.5, 4.5, 5.5, 7.5]:
            # Home covers if D + spread > 0
            p_home_cover = normal_cdf((mu_diff + spread) / sigma_diff)
            p_away_cover = max(0.0, 1.0 - p_home_cover)
            label = f"Spread {spread:+.1f}"
            key = f"spread_{str(spread).replace('.', '_').replace('-', 'minus_').replace('+', 'plus_')}"
            markets[key] = MarketPrediction(
                market_key=key,
                market_label=label,
                outcomes={"home": round(p_home_cover, 5), "away": round(p_away_cover, 5)},
            )

        # Totals Over/Under (e.g. 210.5, 215.5, 220.5, 224.5, 228.5)
        rounded_mid_total = round(mu_tot)
        lines = [
            rounded_mid_total - 10.5,
            rounded_mid_total - 5.5,
            rounded_mid_total - 2.5,
            rounded_mid_total + 2.5,
            rounded_mid_total + 5.5,
            rounded_mid_total + 10.5,
        ]
        for line in lines:
            p_over = normal_cdf((mu_tot - line) / sigma_tot)
            p_under = max(0.0, 1.0 - p_over)
            key = f"total_{str(line).replace('.', '_')}"
            markets[key] = MarketPrediction(
                market_key=key,
                market_label=f"Total Points Over/Under {line}",
                outcomes={"over": round(p_over, 5), "under": round(p_under, 5)},
            )

        breakdown = {
            "expected_pace": round(exp_pace, 2),
            "league_avg_pace": round(ctx.league_avg_pace, 2),
            "ortg_home": round(ortg_h, 2),
            "drtg_home": round(drtg_h, 2),
            "ortg_away": round(ortg_a, 2),
            "drtg_away": round(drtg_a, 2),
            "mu_points_home": round(mu_h, 2),
            "mu_points_away": round(mu_a, 2),
            "sigma_diff": round(sigma_diff, 2),
            "sigma_tot": round(sigma_tot, 2),
            "home_court_advantage_pts": round(hca_pts, 2),
        }

        return SportPredictionResult(
            event_id=ctx.event_id,
            sport="basketball",
            model_version=cls.MODEL_VERSION,
            markets=markets,
            breakdown=breakdown,
        )

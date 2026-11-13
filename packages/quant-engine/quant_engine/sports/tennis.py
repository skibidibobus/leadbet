"""Tennis Markov chain model with Surface Elo, point-to-game, game-to-set, and Bo3/Bo5 match trees."""
from __future__ import annotations

from typing import Any, Dict, Optional, Tuple
import numpy as np

from quant_engine.sports.base import (
    CompetitorInput,
    MarketPrediction,
    MatchContext,
    SportPredictionResult,
)


def point_to_game_prob(p: float) -> float:
    """Exact point-to-game Markov probability with absorbing deuce resolution.

    g(p) = p^4 (15 - 24p + 10p^2) + 20 * p^5 * (1 - p)^3 / (p^2 + (1 - p)^2).
    Satisfies g(0.5) == 0.500000 exactly.
    """
    if p <= 0.0:
        return 0.0
    if p >= 1.0:
        return 1.0

    p2 = p * p
    p4 = p2 * p2
    q = 1.0 - p
    q2 = q * q
    q3 = q2 * q

    # Pre-deuce win probability (love, 15, 30):
    pre_deuce = p4 * (15.0 - 24.0 * p + 10.0 * p2)

    # Deuce arrival and absorption:
    denom = p2 + q2
    deuce = (20.0 * p4 * p * q3) / denom if denom > 0.0 else 0.5

    return float(np.clip(pre_deuce + deuce, 0.0, 1.0))


def compute_tiebreak_prob(p_a: float, p_b: float) -> float:
    """Markov chain for standard 7-point tie-break (win by 2).

    Server sequence:
    Point 0: A serves
    Point 1, 2: B serves
    Point 3, 4: A serves
    ...
    At 6-6: Deuce resolution requires 2-point margin with alternating service.
    """
    # DP state: dp[pt_a, pt_b] = probability A reaches this state from (0, 0)
    # Total points n = pt_a + pt_b
    # Server at point n: A serves if n == 0 or ((n - 1) // 2) % 2 == 1 else B serves
    def server_is_a(n: int) -> bool:
        if n == 0:
            return True
        cycle = (n - 1) // 2
        return cycle % 2 == 1

    # Probability of A winning from 6-6 deuce state:
    # A wins a mini-pair (point on A serve, point on B serve):
    # p_win_pair = p_a * (1.0 - p_b)
    # p_lose_pair = (1.0 - p_a) * p_b
    p_win_pair = p_a * (1.0 - p_b)
    p_lose_pair = (1.0 - p_a) * p_b
    pair_denom = p_win_pair + p_lose_pair
    p_a_from_66 = p_win_pair / pair_denom if pair_denom > 0 else 0.5

    # DP over grid 0..7
    dp = np.zeros((8, 8), dtype=np.float64)
    dp[0, 0] = 1.0

    p_a_wins_tb = 0.0

    for a in range(7):
        for b in range(7):
            state_p = dp[a, b]
            if state_p <= 0.0:
                continue

            n = a + b
            p_win_point = p_a if server_is_a(n) else (1.0 - p_b)

            # A wins point
            if a + 1 == 7 and b < 6:
                p_a_wins_tb += state_p * p_win_point
            else:
                dp[a + 1, b] += state_p * p_win_point

            # B wins point
            if b + 1 == 7 and a < 6:
                pass  # B wins tie-break directly
            else:
                dp[a, b + 1] += state_p * (1.0 - p_win_point)

    # Add probability of arriving at 6-6 and then winning from deuce
    p_reach_66 = dp[6, 6]
    p_a_wins_tb += p_reach_66 * p_a_from_66

    return float(np.clip(p_a_wins_tb, 0.0, 1.0))


def compute_set_prob(p_game_a: float, p_game_b: float, p_tb_a: float) -> float:
    """Compute probability that player A wins a set, averaged over who serves first."""
    def set_prob_conditional(a_serves_first: bool) -> float:
        # dp[g_a, g_b] = probability of reaching score (g_a, g_b)
        dp = np.zeros((8, 8), dtype=np.float64)
        dp[0, 0] = 1.0
        p_a_wins_set = 0.0

        for a in range(7):
            for b in range(7):
                state_p = dp[a, b]
                if state_p <= 0.0:
                    continue

                total_games = a + b
                # Determine who serves game (a + b)
                a_serves = a_serves_first if (total_games % 2 == 0) else not a_serves_first
                p_a_wins_game = p_game_a if a_serves else (1.0 - p_game_b)

                # Game to A
                if a + 1 >= 6 and (a + 1 - b) >= 2:
                    p_a_wins_set += state_p * p_a_wins_game
                elif a + 1 == 6 and b == 6:
                    dp[6, 6] += state_p * p_a_wins_game
                else:
                    dp[a + 1, b] += state_p * p_a_wins_game

                # Game to B
                if b + 1 >= 6 and (b + 1 - a) >= 2:
                    pass  # B wins set
                elif a == 6 and b + 1 == 6:
                    dp[6, 6] += state_p * (1.0 - p_a_wins_game)
                else:
                    dp[a, b + 1] += state_p * (1.0 - p_a_wins_game)

        # 6-6 Tie-break
        p_a_wins_set += dp[6, 6] * p_tb_a
        return p_a_wins_set

    # Unconditional average (50% chance A serves first game)
    p_set = 0.5 * set_prob_conditional(True) + 0.5 * set_prob_conditional(False)
    return float(np.clip(p_set, 0.0, 1.0))


class TennisModel:
    """Surface-specific Elo + point-to-match Markov chain model."""

    MODEL_VERSION = "tennis_markov_surface_v1"
    DEFAULT_TOUR_AVG_SERVE = 0.63
    DEFAULT_ELO = 1500.0

    @classmethod
    def calculate_serve_probabilities(
        cls,
        competitor_a: CompetitorInput,
        competitor_b: CompetitorInput,
        surface: str = "Hard",
        tour_avg_serve: float = DEFAULT_TOUR_AVG_SERVE,
    ) -> tuple[float, float, float, float]:
        """Compute point winning probabilities on serve for player A and player B."""
        # Surface Elo shrinkage
        elo_a = competitor_a.surface_elo or competitor_a.elo or cls.DEFAULT_ELO
        elo_b = competitor_b.surface_elo or competitor_b.elo or cls.DEFAULT_ELO

        # Elo rating differential impact on serve win pct
        # +100 Elo points ~ +2.5% serve point win rate advantage
        elo_diff = elo_a - elo_b
        elo_shift_a = (elo_diff / 400.0) * 0.05
        elo_shift_b = -elo_shift_a

        # Baseline serve/return win percentages
        s_a = competitor_a.serve_win_pct if competitor_a.serve_win_pct is not None else tour_avg_serve
        r_b = competitor_b.return_win_pct if competitor_b.return_win_pct is not None else (1.0 - tour_avg_serve)
        p_a = s_a + (1.0 - r_b) - tour_avg_serve + elo_shift_a

        s_b = competitor_b.serve_win_pct if competitor_b.serve_win_pct is not None else tour_avg_serve
        r_a = competitor_a.return_win_pct if competitor_a.return_win_pct is not None else (1.0 - tour_avg_serve)
        p_b = s_b + (1.0 - r_a) - tour_avg_serve + elo_shift_b

        # Enforce realistic bounds [0.35, 0.95]
        p_a = float(np.clip(p_a, 0.35, 0.95))
        p_b = float(np.clip(p_b, 0.35, 0.95))

        return p_a, p_b, elo_a, elo_b

    @classmethod
    def predict(cls, ctx: MatchContext) -> SportPredictionResult:
        """Execute Tennis Markov simulation across points, games, sets, and match."""
        surface = ctx.surface_or_format or "Hard"
        format_param = ctx.explicit_params.get("format", "Bo3")
        is_bo5 = "bo5" in str(format_param).lower() or "bo5" in str(ctx.surface_or_format).lower()

        p_serve_a, p_serve_b, elo_a, elo_b = cls.calculate_serve_probabilities(
            competitor_a=ctx.home_competitor,
            competitor_b=ctx.away_competitor,
            surface=surface,
        )

        p_game_a = point_to_game_prob(p_serve_a)
        p_game_b = point_to_game_prob(p_serve_b)

        p_tb_a = compute_tiebreak_prob(p_serve_a, p_serve_b)
        p_set_a = compute_set_prob(p_game_a, p_game_b, p_tb_a)
        p_set_b = 1.0 - p_set_a

        markets: Dict[str, MarketPrediction] = {}
        correct_sets_outcomes: Dict[str, float] = {}

        if not is_bo5:
            # Best of 3 sets (first to 2)
            p_2_0 = p_set_a**2
            p_2_1 = 2.0 * (p_set_a**2) * p_set_b
            p_1_2 = 2.0 * p_set_a * (p_set_b**2)
            p_0_2 = p_set_b**2

            p_match_a = p_2_0 + p_2_1
            p_match_b = p_1_2 + p_0_2

            correct_sets_outcomes = {
                "2:0": round(p_2_0, 5),
                "2:1": round(p_2_1, 5),
                "1:2": round(p_1_2, 5),
                "0:2": round(p_0_2, 5),
            }

            # Set Handicap -1.5 / +1.5
            p_handicap_minus_1_5 = p_2_0
            p_handicap_plus_1_5 = 1.0 - p_0_2
        else:
            # Best of 5 sets (first to 3)
            p_3_0 = p_set_a**3
            p_3_1 = 3.0 * (p_set_a**3) * p_set_b
            p_3_2 = 6.0 * (p_set_a**3) * (p_set_b**2)
            p_2_3 = 6.0 * (p_set_a**2) * (p_set_b**3)
            p_1_3 = 3.0 * p_set_a * (p_set_b**3)
            p_0_3 = p_set_b**3

            p_match_a = p_3_0 + p_3_1 + p_3_2
            p_match_b = p_2_3 + p_1_3 + p_0_3

            correct_sets_outcomes = {
                "3:0": round(p_3_0, 5),
                "3:1": round(p_3_1, 5),
                "3:2": round(p_3_2, 5),
                "2:3": round(p_2_3, 5),
                "1:3": round(p_1_3, 5),
                "0:3": round(p_0_3, 5),
            }

            p_handicap_minus_1_5 = p_3_0 + p_3_1
            p_handicap_plus_1_5 = 1.0 - (p_0_3 + p_1_3)

        markets["match_winner"] = MarketPrediction(
            market_key="match_winner",
            market_label="Match Winner",
            outcomes={"player_a": round(p_match_a, 5), "player_b": round(p_match_b, 5)},
        )

        markets["set_handicap_1_5"] = MarketPrediction(
            market_key="set_handicap_1_5",
            market_label="Set Handicap (+/- 1.5)",
            outcomes={
                "player_a": round(p_handicap_minus_1_5, 5),
                "player_b": round(1.0 - p_handicap_minus_1_5, 5),
            },
        )

        markets["correct_sets"] = MarketPrediction(
            market_key="correct_sets",
            market_label="Correct Sets Score",
            outcomes=correct_sets_outcomes,
        )

        breakdown = {
            "surface": surface,
            "match_format": "Bo5" if is_bo5 else "Bo3",
            "p_serve_player_a": round(p_serve_a, 4),
            "p_serve_player_b": round(p_serve_b, 4),
            "p_game_a": round(p_game_a, 4),
            "p_game_b": round(p_game_b, 4),
            "p_tiebreak_a": round(p_tb_a, 4),
            "p_set_a": round(p_set_a, 4),
            "player_a_surface_elo": round(elo_a, 1),
            "player_b_surface_elo": round(elo_b, 1),
        }

        return SportPredictionResult(
            event_id=ctx.event_id,
            sport="tennis",
            model_version=cls.MODEL_VERSION,
            markets=markets,
            breakdown=breakdown,
        )

"""Base classes, data contracts, and common errors for sports models."""
from __future__ import annotations

import os
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class FeatureNotEnabledError(RuntimeError):
    """Raised when attempting to access a feature or sport gated by a disabled feature flag."""


def is_phase2_enabled() -> bool:
    """Check whether Phase 2 sports (Volleyball, Table Tennis) are enabled."""
    return os.environ.get("ENABLE_PHASE2_SPORTS", "false").lower() in ("true", "1", "yes")


class CompetitorInput(BaseModel):
    """Input statistics and ratings for a competitor/team."""

    competitor_id: str
    name: str
    elo: Optional[float] = None
    surface_elo: Optional[float] = None
    glicko_r: Optional[float] = None
    glicko_rd: Optional[float] = None
    glicko_sigma: Optional[float] = None
    xg_attack: Optional[float] = None
    xg_defense: Optional[float] = None
    goals_attack: Optional[float] = None
    goals_defense: Optional[float] = None
    pace: Optional[float] = None
    ortg: Optional[float] = None
    drtg: Optional[float] = None
    rest_days: Optional[int] = None
    serve_win_pct: Optional[float] = None
    return_win_pct: Optional[float] = None


class MatchContext(BaseModel):
    """Context and parameters required for a match simulation."""

    event_id: str
    sport: str
    home_competitor: CompetitorInput
    away_competitor: CompetitorInput
    surface_or_format: Optional[str] = None  # e.g. "Hard", "Clay", "Bo3", "Bo5"
    league_avg_xg: float = 1.35
    league_avg_goals: float = 1.40
    league_avg_pace: float = 100.0
    league_avg_rtg: float = 112.0
    explicit_params: Dict[str, Any] = Field(default_factory=dict)


class MarketPrediction(BaseModel):
    """Probability distribution over discrete outcomes for a specific betting market."""

    market_key: str
    market_label: str
    outcomes: Dict[str, float]


class SportPredictionResult(BaseModel):
    """Standardized prediction output from any sports model."""

    event_id: str
    sport: str
    model_version: str
    markets: Dict[str, MarketPrediction]
    breakdown: Dict[str, Any]

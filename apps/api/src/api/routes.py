"""REST API endpoints for QUANTKUPON (/api/v1/*)."""
from __future__ import annotations

from typing import Any, Dict, List, Optional, Union
from fastapi import APIRouter, HTTPException, Query, status
from pydantic import BaseModel, Field

from bookmaker_adapters.tax.polish_tax import BookmakerMode
from quant_engine.optimizer.slip_optimizer import SlipGenerateParams
from src.services.data_service import QuantDataService

router = APIRouter(prefix="/api/v1", tags=["LeadBet"])

# Process-wide service instance (pre-match snapshot / DB backed)
_service = QuantDataService()


class LegInput(BaseModel):
    """Single selection input for slip evaluation or saving."""

    event_id: str
    market_key: str
    outcome_key: str
    bookmaker_key: Optional[str] = None
    odds_override: Optional[float] = Field(default=None, ge=1.01)


class SlipEvaluateRequest(BaseModel):
    """Request payload for POST /api/v1/slips/evaluate."""

    selections: List[LegInput] = Field(..., min_length=1)
    stake: float = Field(..., ge=1.0)
    bookmaker_mode: Union[BookmakerMode, str] = BookmakerMode.BETCLIC_TAX_FREE


class SaveSlipRequest(BaseModel):
    """Request payload for POST /api/v1/slips/saved."""

    name: Optional[str] = None
    selections: List[LegInput] = Field(..., min_length=1)
    stake: float = Field(..., ge=1.0)
    bookmaker_mode: Union[BookmakerMode, str] = BookmakerMode.BETCLIC_TAX_FREE
    bookmaker_key: Optional[str] = "betclic"


@router.get("/categories")
async def list_categories(
    enabled_only: bool = Query(default=False),
) -> Dict[str, Any]:
    """List supported sport categories and active phase flags."""
    return _service.get_categories(enabled_only=enabled_only)


@router.get("/events")
async def list_events(
    sport: Optional[str] = Query(default=None),
    league_id: Optional[int] = Query(default=None),
    market: Optional[str] = Query(default=None),
    min_ev: Optional[float] = Query(default=None),
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
) -> Dict[str, Any]:
    """List pre-match events with de-vigged probabilities and net EV."""
    return _service.get_events(
        sport=sport,
        league_id=league_id,
        market=market,
        min_ev=min_ev,
        limit=limit,
        offset=offset,
    )


@router.get("/events/{event_id}/breakdown")
async def get_event_breakdown(event_id: str) -> Dict[str, Any]:
    """Return mathematical breakdown (model vs sharp vs Polish market) for an event."""
    breakdown = _service.get_event_breakdown(event_id)
    if breakdown is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Event '{event_id}' not found",
        )
    return breakdown


@router.post("/slips/generate")
async def generate_slips(params: SlipGenerateParams) -> Dict[str, Any]:
    """Generate optimal multi-leg coupons maximizing P(coupon) within target odds."""
    return _service.generate_slips(params)


@router.post("/slips/evaluate")
async def evaluate_slip(payload: SlipEvaluateRequest) -> Dict[str, Any]:
    """Evaluate a custom or user-overridden slip with Polish tax & PIT calculation."""
    legs = [leg.model_dump() for leg in payload.selections]
    mode = payload.bookmaker_mode.value if isinstance(payload.bookmaker_mode, BookmakerMode) else payload.bookmaker_mode
    return _service.evaluate_slip(
        legs=legs,
        stake=payload.stake,
        bookmaker_mode=mode,
    )


@router.get("/slips/saved")
async def list_saved_slips(
    user_id: Optional[str] = Query(default=None),
) -> Dict[str, Any]:
    """List saved slips."""
    return _service.list_saved_slips(user_id=user_id)


@router.post("/slips/saved", status_code=status.HTTP_201_CREATED)
async def save_slip(payload: SaveSlipRequest) -> Dict[str, Any]:
    """Save an evaluated slip."""
    mode = payload.bookmaker_mode.value if isinstance(payload.bookmaker_mode, BookmakerMode) else payload.bookmaker_mode
    return _service.save_slip(
        {
            "name": payload.name,
            "selections": [leg.model_dump() for leg in payload.selections],
            "stake": payload.stake,
            "bookmaker_mode": mode,
            "bookmaker_key": payload.bookmaker_key,
        }
    )


@router.delete("/slips/saved/{slip_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_saved_slip(slip_id: str) -> None:
    """Delete a saved slip by ID."""
    deleted = _service.delete_saved_slip(slip_id)
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Saved slip '{slip_id}' not found",
        )


@router.get("/calibration/metrics")
async def get_calibration_metrics(
    time_horizon: str = Query(default="90d"),
) -> Dict[str, Any]:
    """Return historical model calibration metrics (Brier, LogLoss, ECE, CLV)."""
    return _service.get_calibration_metrics(time_horizon=time_horizon)

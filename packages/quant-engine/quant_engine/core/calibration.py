"""Model calibration auditing and reliability metrics.

Implements:
- Brier Score and Brier Skill Score (BSS).
- Binary cross-entropy (Log-Loss) with strict 1e-15 clipping.
- Closing Line Value (CLV) beat rate and average percentage metrics.
- 10-bin Reliability Diagram decile breakdown conforming to OpenAPI 3.1 specification.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Optional, Sequence
import numpy as np


@dataclass(frozen=True)
class CalibrationBinData:
    """Reliability diagram bin matching CalibrationBin schema in openapi.yaml."""

    bin_index: int
    predicted_prob_lower: float
    predicted_prob_upper: float
    mean_predicted_prob: float
    empirical_win_rate: float
    sample_count: int
    brier_contribution: float


@dataclass(frozen=True)
class CalibrationMetricsSummaryData:
    """Summary calibration metrics matching CalibrationMetricsSummary schema."""

    sample_size: int
    brier_score: float
    brier_skill_score: float
    log_loss: float
    clv_beat_rate: float
    avg_clv_percentage: float
    reliability_bins: list[CalibrationBinData]


def compute_brier_score(p_pred: Sequence[float], y_true: Sequence[int | float]) -> float:
    """Compute mean squared error Brier Score."""
    if len(p_pred) != len(y_true):
        raise ValueError(f"Length mismatch: {len(p_pred)} predictions vs {len(y_true)} outcomes")
    if len(p_pred) == 0:
        raise ValueError("Cannot compute Brier Score on empty inputs")
    p = np.asarray(p_pred, dtype=np.float64)
    y = np.asarray(y_true, dtype=np.float64)
    return float(np.mean((p - y) ** 2))


def compute_brier_skill_score(p_pred: Sequence[float], y_true: Sequence[int | float]) -> float:
    """Compute Brier Skill Score (BSS) against climatological base rate."""
    if len(p_pred) != len(y_true):
        raise ValueError(f"Length mismatch: {len(p_pred)} predictions vs {len(y_true)} outcomes")
    if len(p_pred) == 0:
        raise ValueError("Cannot compute Brier Skill Score on empty inputs")
    p = np.asarray(p_pred, dtype=np.float64)
    y = np.asarray(y_true, dtype=np.float64)
    bs = float(np.mean((p - y) ** 2))
    base_rate = float(np.mean(y))
    bs_ref = base_rate * (1.0 - base_rate)
    if bs_ref < 1e-12:
        return 0.0
    return float(1.0 - (bs / bs_ref))


def compute_log_loss(
    p_pred: Sequence[float],
    y_true: Sequence[int | float],
    eps: float = 1e-15,
) -> float:
    """Compute binary cross-entropy (Log-Loss) with probability clipping at [eps, 1-eps]."""
    if len(p_pred) != len(y_true):
        raise ValueError(f"Length mismatch: {len(p_pred)} predictions vs {len(y_true)} outcomes")
    if len(p_pred) == 0:
        raise ValueError("Cannot compute Log-Loss on empty inputs")
    p = np.asarray(p_pred, dtype=np.float64)
    y = np.asarray(y_true, dtype=np.float64)
    p_clipped = np.clip(p, eps, 1.0 - eps)
    return float(-np.mean(y * np.log(p_clipped) + (1.0 - y) * np.log(1.0 - p_clipped)))


def compute_clv_metrics(
    odds_taken: Sequence[float],
    closing_sharp_odds: Sequence[float],
) -> tuple[float, float]:
    """Compute Closing Line Value metrics: (clv_beat_rate, avg_clv_percentage)."""
    if len(odds_taken) != len(closing_sharp_odds):
        raise ValueError(
            f"Length mismatch: {len(odds_taken)} taken vs {len(closing_sharp_odds)} closing"
        )
    if len(odds_taken) == 0:
        return 0.0, 0.0
    ot = np.asarray(odds_taken, dtype=np.float64)
    oc = np.asarray(closing_sharp_odds, dtype=np.float64)
    deltas = (ot / oc) - 1.0
    beat_rate = float(np.mean(deltas > 0))
    avg_pct = float(np.mean(deltas))
    return beat_rate, avg_pct


def compute_reliability_bins(
    p_pred: Sequence[float],
    y_true: Sequence[int | float],
    num_bins: int = 10,
) -> list[CalibrationBinData]:
    """Calculate decile reliability diagram bins."""
    if len(p_pred) != len(y_true):
        raise ValueError(f"Length mismatch: {len(p_pred)} predictions vs {len(y_true)} outcomes")
    p = np.asarray(p_pred, dtype=np.float64)
    y = np.asarray(y_true, dtype=np.float64)
    n = len(p)
    bins = []

    for b in range(num_bins):
        lower = b / num_bins
        upper = (b + 1) / num_bins
        if b == num_bins - 1:
            mask = (p >= lower) & (p <= upper)
        else:
            mask = (p >= lower) & (p < upper)

        count = int(np.sum(mask))
        if count > 0:
            mean_p = float(np.mean(p[mask]))
            win_rate = float(np.mean(y[mask]))
            brier_contrib = float(np.sum((p[mask] - y[mask]) ** 2) / (n if n > 0 else 1))
        else:
            mean_p = (lower + upper) / 2.0
            win_rate = 0.0
            brier_contrib = 0.0

        bins.append(
            CalibrationBinData(
                bin_index=b,
                predicted_prob_lower=round(lower, 2),
                predicted_prob_upper=round(upper, 2),
                mean_predicted_prob=round(mean_p, 4),
                empirical_win_rate=round(win_rate, 4),
                sample_count=count,
                brier_contribution=round(brier_contrib, 6),
            )
        )
    return bins


def evaluate_calibration(
    p_pred: Sequence[float],
    y_true: Sequence[int | float],
    odds_taken: Optional[Sequence[float]] = None,
    closing_sharp_odds: Optional[Sequence[float]] = None,
) -> CalibrationMetricsSummaryData:
    """Consolidated calibration evaluation matching backend and contract schemas."""
    n = len(p_pred)
    bs = compute_brier_score(p_pred, y_true)
    bss = compute_brier_skill_score(p_pred, y_true)
    ll = compute_log_loss(p_pred, y_true)

    if odds_taken is not None and closing_sharp_odds is not None:
        beat_rate, avg_clv = compute_clv_metrics(odds_taken, closing_sharp_odds)
    else:
        beat_rate, avg_clv = 0.0, 0.0

    bins = compute_reliability_bins(p_pred, y_true, num_bins=10)

    return CalibrationMetricsSummaryData(
        sample_size=n,
        brier_score=round(bs, 4),
        brier_skill_score=round(bss, 4),
        log_loss=round(ll, 4),
        clv_beat_rate=round(beat_rate, 4),
        avg_clv_percentage=round(avg_clv, 4),
        reliability_bins=bins,
    )

"""QUANTKUPON Quantitative Engine Core Mathematical Algorithms."""
from __future__ import annotations

from quant_engine.core.solvers import brentq_pure, find_root_brent
from quant_engine.core.devig import (
    DevigResult,
    NegativeVigError,
    devig,
    devig_multiplicative,
    devig_power,
    devig_shin,
    devig_shin_detailed,
)
from quant_engine.core.bayesian import (
    SPORT_MODEL_WEIGHTS,
    fuse_market_probabilities,
)
from quant_engine.core.kelly import (
    calculate_kelly_fraction,
    calculate_kelly_fraction_pl,
    calculate_kelly_stake,
)
from quant_engine.core.calibration import (
    CalibrationBinData,
    CalibrationMetricsSummaryData,
    compute_brier_score,
    compute_brier_skill_score,
    compute_clv_metrics,
    compute_log_loss,
    compute_reliability_bins,
    evaluate_calibration,
)

__all__ = [
    "brentq_pure",
    "find_root_brent",
    "DevigResult",
    "NegativeVigError",
    "devig",
    "devig_multiplicative",
    "devig_power",
    "devig_shin",
    "devig_shin_detailed",
    "SPORT_MODEL_WEIGHTS",
    "fuse_market_probabilities",
    "calculate_kelly_fraction",
    "calculate_kelly_fraction_pl",
    "calculate_kelly_stake",
    "CalibrationBinData",
    "CalibrationMetricsSummaryData",
    "compute_brier_score",
    "compute_brier_skill_score",
    "compute_clv_metrics",
    "compute_log_loss",
    "compute_reliability_bins",
    "evaluate_calibration",
]

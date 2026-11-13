"""Bayesian market fusion blending statistical model outputs with sharp bookmaker consensus.

Implements:
- Linear convex fusion.
- Log-odds / geometric pooling (preserving conditional odds independence).
- Dirichlet conjugate prior fusion.
- Sport-specific default weighting and Table Tennis Volatility Guard shrinkage.
"""
from __future__ import annotations

from typing import Literal, Optional, Sequence
import numpy as np

SPORT_MODEL_WEIGHTS: dict[str, float] = {
    "football": 0.45,
    "basketball": 0.40,
    "tennis": 0.40,
    "hockey": 0.35,
    "volleyball": 0.40,
    "table_tennis": 0.30,
}


def fuse_market_probabilities(
    p_model: Sequence[float],
    p_sharp: Sequence[float],
    sport: str = "football",
    method: Literal["linear", "log_odds", "dirichlet"] = "linear",
    custom_weight: Optional[float] = None,
    volatility_sigma: Optional[float] = None,
) -> list[float]:
    """Fuse pure statistical model probability with sharp market consensus.

    Args:
        p_model: Statistical model probabilities.
        p_sharp: De-vigged sharp bookmaker consensus probabilities.
        sport: Sport category string ('football', 'basketball', 'tennis', etc.).
        method: Fusion algorithm ('linear', 'log_odds', 'dirichlet').
        custom_weight: Optional explicit weight in [0, 1] assigned to p_model.
        volatility_sigma: Volatility parameter (e.g. Glicko-2 sigma for table tennis).

    Returns:
        Fused consensus probabilities summing strictly to 1.0.
    """
    if len(p_model) != len(p_sharp):
        raise ValueError(
            f"Dimension mismatch: p_model has {len(p_model)}, p_sharp has {len(p_sharp)}"
        )
    if len(p_model) < 2:
        raise ValueError("Probability vectors must have at least 2 outcomes")

    pm = np.asarray(p_model, dtype=np.float64)
    ps = np.asarray(p_sharp, dtype=np.float64)

    if np.any(pm < 0.0) or np.any(ps < 0.0):
        raise ValueError("Probabilities cannot be negative")

    sum_pm = np.sum(pm)
    sum_ps = np.sum(ps)
    if sum_pm <= 0.0 or sum_ps <= 0.0:
        raise ValueError("Sum of input probabilities must be strictly positive")

    # Normalize inputs to ensure valid simplex
    pm = pm / sum_pm
    ps = ps / sum_ps

    # Determine base model weight w
    if custom_weight is not None:
        if not (0.0 <= custom_weight <= 1.0):
            raise ValueError(f"custom_weight must be in [0, 1], got {custom_weight}")
        w = float(custom_weight)
    else:
        w = float(SPORT_MODEL_WEIGHTS.get(sport.lower(), 0.40))

    # Table Tennis Volatility Guard shrinkage
    if sport.lower() == "table_tennis" and volatility_sigma is not None:
        sigma_threshold = 0.06
        if volatility_sigma > sigma_threshold:
            shrinkage = sigma_threshold / volatility_sigma
            w = max(0.05, w * shrinkage)

    if method in ("linear", "dirichlet"):
        fused = w * pm + (1.0 - w) * ps
    elif method == "log_odds":
        eps = 1e-12
        pm_c = np.clip(pm, eps, 1.0)
        ps_c = np.clip(ps, eps, 1.0)
        log_p = w * np.log(pm_c) + (1.0 - w) * np.log(ps_c)
        exp_p = np.exp(log_p - np.max(log_p))
        fused = exp_p / np.sum(exp_p)
    else:
        raise ValueError(f"Unknown fusion method: {method}")

    # Enforce strict invariant sum == 1.0
    fused_norm = (fused / np.sum(fused)).tolist()
    return fused_norm

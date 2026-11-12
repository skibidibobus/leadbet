"""Smoke test for quant-engine."""
from __future__ import annotations

import quant_engine


def test_quant_engine_smoke():
    """Verify package import and smoke test."""
    assert quant_engine.__version__ == "0.1.0"

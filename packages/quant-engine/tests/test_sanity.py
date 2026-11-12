"""Sanity and version tests for quant-engine."""
from __future__ import annotations

import quant_engine


def test_quant_engine_sanity():
    """Verify package import and version definition."""
    assert quant_engine.__version__ == "0.1.0"

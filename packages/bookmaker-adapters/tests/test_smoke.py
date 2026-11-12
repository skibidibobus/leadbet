"""Smoke test for bookmaker-adapters."""
from __future__ import annotations

import bookmaker_adapters


def test_bookmaker_adapters_smoke():
    """Verify package import and smoke test."""
    assert bookmaker_adapters.__version__ == "0.1.0"

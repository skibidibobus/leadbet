"""Sanity and version tests for bookmaker-adapters."""
from __future__ import annotations

import bookmaker_adapters


def test_bookmaker_adapters_sanity():
    """Verify package import and version definition."""
    assert bookmaker_adapters.__version__ == "0.1.0"

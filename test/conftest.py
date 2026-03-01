"""
Shared fixtures for crypto_analyzer tests.
"""

import sys
import os
import pytest
import pandas as pd
import numpy as np

# Ensure project root is on Python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


@pytest.fixture
def sample_ohlcv_df():
    """30-row OHLCV DataFrame mimicking real crypto data."""
    np.random.seed(42)
    dates = pd.date_range("2026-01-01", periods=30, freq="h")
    close_base = 2000.0
    closes = close_base + np.cumsum(np.random.randn(30) * 20)

    df = pd.DataFrame({
        "Open":   closes - np.random.rand(30) * 10,
        "High":   closes + np.random.rand(30) * 30,
        "Low":    closes - np.random.rand(30) * 30,
        "Close":  closes,
        "Volume": np.random.randint(100_000, 1_000_000, size=30).astype(float),
    }, index=dates)
    return df


@pytest.fixture
def empty_df():
    """Empty DataFrame for edge-case tests."""
    return pd.DataFrame()


@pytest.fixture
def sample_stats():
    """Typical stats dict as returned by get_ticker_stats."""
    return {
        "price": 2500.0,
        "high_24h": 2550.0,
        "change_24h": 25.0,
        "change_pct": 1.01,
        "volume_24h": 12_345_678.0,
        "market_cap": 300_000_000_000.0,
    }

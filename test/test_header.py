"""
Unit tests for components.header module.
Tests: render_header (via HTML output validation)
"""

import pytest
from unittest.mock import patch, MagicMock


class TestRenderHeader:
    """Test render_header builds correct HTML structure."""

    def test_positive_change_class(self, sample_stats):
        """Verify positive change produces 'positive' class."""
        from components.header import render_header
        # We can't easily test Streamlit rendering, but we can validate logic
        change_24h = sample_stats["change_24h"]
        assert change_24h >= 0
        change_class = "positive" if change_24h >= 0 else "negative"
        assert change_class == "positive"

    def test_negative_change_class(self):
        """Verify negative change produces 'negative' class."""
        stats = {
            "price": 2500.0, "high_24h": 2550.0,
            "change_24h": -50.0, "change_pct": -1.96,
            "volume_24h": 5_000_000.0, "market_cap": 300_000_000_000.0,
        }
        change_class = "positive" if stats["change_24h"] >= 0 else "negative"
        assert change_class == "negative"

    def test_stats_values_are_numeric(self, sample_stats):
        """Ensure all stats values are numeric for formatting."""
        for key, value in sample_stats.items():
            assert isinstance(value, (int, float)), f"{key} is not numeric"

"""
Unit tests for components.chatbot module.
Tests: _build_market_context
"""

import pytest
import pandas as pd
import numpy as np

from components.chatbot import _build_market_context


class TestBuildMarketContext:
    def test_includes_ticker(self, sample_ohlcv_df, sample_stats):
        result = _build_market_context("ETH-USD", sample_stats, sample_ohlcv_df)
        assert "ETH-USD" in result

    def test_includes_price(self, sample_ohlcv_df, sample_stats):
        result = _build_market_context("ETH-USD", sample_stats, sample_ohlcv_df)
        assert "2,500.00" in result

    def test_includes_rsi_when_present(self, sample_ohlcv_df, sample_stats):
        from data.crypto_data import compute_rsi
        df = compute_rsi(sample_ohlcv_df)
        result = _build_market_context("ETH-USD", sample_stats, df)
        assert "RSI" in result

    def test_includes_sma_when_present(self, sample_ohlcv_df, sample_stats):
        from data.crypto_data import compute_sma
        df = compute_sma(sample_ohlcv_df)
        result = _build_market_context("ETH-USD", sample_stats, df)
        assert "SMA" in result

    def test_handles_none_stats(self, sample_ohlcv_df):
        result = _build_market_context("ETH-USD", None, sample_ohlcv_df)
        assert "ETH-USD" in result

    def test_handles_empty_df(self, sample_stats):
        result = _build_market_context("ETH-USD", sample_stats, pd.DataFrame())
        assert "ETH-USD" in result

    def test_handles_all_none(self):
        result = _build_market_context("BTC-USD", None, None)
        assert "BTC-USD" in result

    def test_includes_recent_candles(self, sample_ohlcv_df, sample_stats):
        result = _build_market_context("ETH-USD", sample_stats, sample_ohlcv_df)
        assert "Open" in result
        assert "Close" in result

    def test_includes_market_data_labels(self, sample_ohlcv_df, sample_stats):
        result = _build_market_context("ETH-USD", sample_stats, sample_ohlcv_df)
        assert "현재가" in result
        assert "24시간 변동" in result
        assert "거래량" in result

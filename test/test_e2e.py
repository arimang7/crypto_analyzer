"""
E2E (End-to-End) Tests for Crypto Analyzer.
Tests the complete data pipeline: fetch → compute → display readiness.
Uses mocked external APIs to ensure deterministic, fast tests.
"""

import pytest
import pandas as pd
import numpy as np
import json
from unittest.mock import patch, MagicMock

from data.crypto_data import (
    get_crypto_list, get_ohlcv, get_ticker_stats,
    compute_sma, compute_rsi, format_number,
)
from data.ai_signal import generate_signals, _fallback_signals
from components.chatbot import _build_market_context
from components.sidebar_copilot import _fallback_result


class TestE2EDataPipeline:
    """Test the full data flow: list → fetch → compute → ready for chart."""

    @patch("data.crypto_data.yf.download")
    @patch("data.crypto_data.yf.Ticker")
    def test_full_pipeline_for_all_cryptos(self, mock_ticker_cls, mock_download, sample_ohlcv_df):
        """E2E: Iterate all cryptos, fetch data, compute indicators, verify output."""
        mock_download.return_value = sample_ohlcv_df
        mock_ticker_cls.return_value.info = {
            "regularMarketPrice": 2500.0,
            "regularMarketPreviousClose": 2450.0,
            "dayHigh": 2550.0,
            "regularMarketVolume": 5_000_000,
            "marketCap": 300_000_000_000,
        }

        crypto_list = get_crypto_list()
        assert len(crypto_list) > 0

        for symbol, ticker in crypto_list.items():
            # 1. Fetch data
            df = get_ohlcv(ticker, interval="1h")
            assert not df.empty, f"Data fetch failed for {ticker}"
            assert "Close" in df.columns

            # 2. Compute indicators
            df = compute_sma(df, window=5)
            df = compute_rsi(df, period=14)
            assert "SMA" in df.columns, f"SMA computation failed for {ticker}"
            assert "RSI" in df.columns, f"RSI computation failed for {ticker}"

            # 3. Get stats
            stats = get_ticker_stats(ticker)
            assert stats["price"] > 0, f"Stats fetch failed for {ticker}"

            # 4. Verify chart-readiness
            assert len(df) >= 5, f"Insufficient data for charting {ticker}"


class TestE2ESignalPipeline:
    """Test the full signal generation pipeline."""

    @patch("data.ai_signal.get_client")
    @patch("data.crypto_data.yf.download")
    def test_signal_generation_e2e(self, mock_download, mock_get_client, sample_ohlcv_df):
        """E2E: Fetch data → compute indicators → generate signals."""
        mock_download.return_value = sample_ohlcv_df

        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.text = json.dumps([
            {"direction": "long", "entry": 1995.0, "take_profit": 2072.0,
             "stop_loss": 1966.0, "style": "Day", "strategy": "최대 수익"},
        ])
        mock_client.models.generate_content.return_value = mock_response
        mock_get_client.return_value = mock_client

        # Pipeline
        df = get_ohlcv("ETH-USD", interval="1h")
        df = compute_sma(df)
        df = compute_rsi(df)

        signals = generate_signals("ETH-USD", df, num_signals=1)

        assert len(signals) >= 1
        assert signals[0]["direction"] in ("long", "short")
        assert signals[0]["entry"] > 0

    @patch("data.crypto_data.yf.download")
    def test_signal_fallback_e2e(self, mock_download, sample_ohlcv_df):
        """E2E: Verify fallback signals work when AI fails."""
        mock_download.return_value = sample_ohlcv_df

        df = get_ohlcv("ETH-USD", interval="1h")
        df = compute_sma(df)
        df = compute_rsi(df)

        current_price = float(df["Close"].iloc[-1])
        signals = _fallback_signals("ETH-USD", current_price)

        assert len(signals) == 2
        assert signals[0]["direction"] == "long"
        assert signals[1]["direction"] == "short"


class TestE2EChatbotPipeline:
    """Test the chatbot context building pipeline."""

    @patch("data.crypto_data.yf.download")
    @patch("data.crypto_data.yf.Ticker")
    def test_chatbot_context_e2e(self, mock_ticker_cls, mock_download, sample_ohlcv_df):
        """E2E: Fetch data → compute all indicators → build AI context."""
        mock_download.return_value = sample_ohlcv_df
        mock_ticker_cls.return_value.info = {
            "regularMarketPrice": 2500.0,
            "regularMarketPreviousClose": 2450.0,
            "dayHigh": 2550.0,
            "regularMarketVolume": 5_000_000,
            "marketCap": 300_000_000_000,
        }

        # Full pipeline
        ticker = "ETH-USD"
        df = get_ohlcv(ticker, interval="1h")
        df = compute_sma(df)
        df = compute_rsi(df)
        stats = get_ticker_stats(ticker)

        # Build context
        context = _build_market_context(ticker, stats, df)

        # Verify context completeness
        assert "ETH-USD" in context
        assert "현재가" in context
        assert "RSI" in context
        assert "SMA" in context
        assert "Open" in context
        assert "Close" in context

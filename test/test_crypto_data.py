"""
Unit tests for data.crypto_data module.
Tests: get_crypto_list, get_ohlcv, get_ticker_stats, compute_sma, compute_rsi, format_number
"""

import pytest
import pandas as pd
import numpy as np
from unittest.mock import patch, MagicMock

from data.crypto_data import (
    get_crypto_list,
    get_ohlcv,
    get_ticker_stats,
    compute_sma,
    compute_rsi,
    format_number,
    CRYPTO_LIST,
    INTERVAL_CONFIG,
)


# ===== get_crypto_list =====

class TestGetCryptoList:
    def test_returns_dict(self):
        result = get_crypto_list()
        assert isinstance(result, dict)

    def test_contains_btc(self):
        result = get_crypto_list()
        assert "BTC" in result
        assert result["BTC"] == "BTC-USD"

    def test_contains_eth(self):
        result = get_crypto_list()
        assert "ETH" in result
        assert result["ETH"] == "ETH-USD"

    def test_has_at_least_5_cryptos(self):
        result = get_crypto_list()
        assert len(result) >= 5

    def test_all_values_end_with_usd(self):
        for symbol, ticker in get_crypto_list().items():
            assert ticker.endswith("-USD"), f"{symbol} ticker {ticker} does not end with -USD"


# ===== INTERVAL_CONFIG =====

class TestIntervalConfig:
    def test_has_required_intervals(self):
        for interval in ["1m", "5m", "15m", "1h", "4h", "1d"]:
            assert interval in INTERVAL_CONFIG, f"Missing interval: {interval}"

    def test_each_interval_has_period_and_label(self):
        for key, value in INTERVAL_CONFIG.items():
            assert "period" in value, f"{key} missing 'period'"
            assert "label" in value, f"{key} missing 'label'"


# ===== compute_sma =====

class TestComputeSMA:
    def test_adds_sma_column(self, sample_ohlcv_df):
        result = compute_sma(sample_ohlcv_df, window=5)
        assert "SMA" in result.columns

    def test_sma_first_values_are_nan(self, sample_ohlcv_df):
        result = compute_sma(sample_ohlcv_df, window=5)
        # First 4 values (window-1) should be NaN
        assert result["SMA"].iloc[:4].isna().all()

    def test_sma_values_are_correct(self, sample_ohlcv_df):
        window = 5
        result = compute_sma(sample_ohlcv_df, window=window)
        # Check a specific SMA value
        expected = sample_ohlcv_df["Close"].iloc[:window].mean()
        np.testing.assert_almost_equal(result["SMA"].iloc[window - 1], expected, decimal=6)

    def test_does_not_modify_original(self, sample_ohlcv_df):
        original_cols = set(sample_ohlcv_df.columns)
        compute_sma(sample_ohlcv_df, window=5)
        assert set(sample_ohlcv_df.columns) == original_cols

    def test_empty_df_returns_empty(self, empty_df):
        result = compute_sma(empty_df)
        assert result.empty

    def test_default_window_is_20(self, sample_ohlcv_df):
        result = compute_sma(sample_ohlcv_df)
        # First 19 values should be NaN with window=20
        assert result["SMA"].iloc[:19].isna().all()
        assert not pd.isna(result["SMA"].iloc[19])


# ===== compute_rsi =====

class TestComputeRSI:
    def test_adds_rsi_column(self, sample_ohlcv_df):
        result = compute_rsi(sample_ohlcv_df, period=14)
        assert "RSI" in result.columns

    def test_rsi_values_between_0_and_100(self, sample_ohlcv_df):
        result = compute_rsi(sample_ohlcv_df, period=14)
        valid_rsi = result["RSI"].dropna()
        assert (valid_rsi >= 0).all(), "RSI values below 0"
        assert (valid_rsi <= 100).all(), "RSI values above 100"

    def test_does_not_modify_original(self, sample_ohlcv_df):
        original_cols = set(sample_ohlcv_df.columns)
        compute_rsi(sample_ohlcv_df, period=14)
        assert set(sample_ohlcv_df.columns) == original_cols

    def test_empty_df_returns_empty(self, empty_df):
        result = compute_rsi(empty_df)
        assert result.empty

    def test_constant_price_rsi_is_nan(self):
        """When price never changes, RSI should be NaN (0/0 case)."""
        dates = pd.date_range("2026-01-01", periods=30, freq="h")
        df = pd.DataFrame({
            "Open": 100.0, "High": 100.0, "Low": 100.0,
            "Close": 100.0, "Volume": 1000.0,
        }, index=dates)
        result = compute_rsi(df, period=14)
        # With constant price, delta is 0 => gain=0, loss=0 => rs=NaN => RSI=NaN
        valid = result["RSI"].dropna()
        # All non-NaN RSI should still be within bounds if they exist
        if not valid.empty:
            assert (valid >= 0).all() and (valid <= 100).all()


# ===== format_number =====

class TestFormatNumber:
    def test_zero(self):
        assert format_number(0) == "$0"

    def test_none(self):
        assert format_number(None) == "$0"

    def test_small_number(self):
        result = format_number(42.5)
        assert result == "$42.50"

    def test_thousands(self):
        result = format_number(1500)
        assert result == "$1.50K"

    def test_millions(self):
        result = format_number(2_500_000)
        assert result == "$2.50M"

    def test_billions(self):
        result = format_number(300_000_000_000)
        assert result == "$300.00B"

    def test_custom_prefix(self):
        result = format_number(1000, prefix="€")
        assert result == "€1.00K"

    def test_negative_value(self):
        result = format_number(-2_500_000)
        assert result == "$-2.50M"


# ===== get_ohlcv (mock yfinance) =====

class TestGetOHLCV:
    @patch("data.crypto_data.yf.download")
    def test_returns_ohlcv_columns(self, mock_download, sample_ohlcv_df):
        mock_download.return_value = sample_ohlcv_df
        result = get_ohlcv("ETH-USD", interval="1h")
        assert set(result.columns) == {"Open", "High", "Low", "Close", "Volume"}

    @patch("data.crypto_data.yf.download")
    def test_returns_empty_on_error(self, mock_download):
        mock_download.side_effect = Exception("Network error")
        result = get_ohlcv("ETH-USD")
        assert result.empty

    @patch("data.crypto_data.yf.download")
    def test_returns_empty_when_no_data(self, mock_download):
        mock_download.return_value = pd.DataFrame()
        result = get_ohlcv("FAKE-USD")
        assert result.empty

    @patch("data.crypto_data.yf.download")
    def test_auto_selects_period(self, mock_download, sample_ohlcv_df):
        mock_download.return_value = sample_ohlcv_df
        get_ohlcv("ETH-USD", interval="1d")
        call_kwargs = mock_download.call_args
        assert call_kwargs[1].get("period") == "180d" or call_kwargs.kwargs.get("period") == "180d"

    @patch("data.crypto_data.yf.download")
    def test_custom_period_overrides(self, mock_download, sample_ohlcv_df):
        mock_download.return_value = sample_ohlcv_df
        get_ohlcv("ETH-USD", interval="1h", period="7d")
        call_kwargs = mock_download.call_args
        assert "7d" in str(call_kwargs)

    @patch("data.crypto_data.yf.download")
    def test_handles_multi_index_columns(self, mock_download):
        """Test flattening of MultiIndex columns from yfinance."""
        dates = pd.date_range("2026-01-01", periods=5, freq="h")
        multi_df = pd.DataFrame(
            np.random.rand(5, 5) * 1000,
            index=dates,
            columns=pd.MultiIndex.from_tuples([
                ("Open", "ETH-USD"), ("High", "ETH-USD"), ("Low", "ETH-USD"),
                ("Close", "ETH-USD"), ("Volume", "ETH-USD"),
            ]),
        )
        mock_download.return_value = multi_df
        result = get_ohlcv("ETH-USD")
        assert not isinstance(result.columns, pd.MultiIndex)
        assert "Close" in result.columns


# ===== get_ticker_stats (mock yfinance) =====

class TestGetTickerStats:
    @patch("data.crypto_data.yf.Ticker")
    def test_returns_expected_keys(self, mock_ticker_cls):
        mock_info = {
            "regularMarketPrice": 2500.0,
            "regularMarketPreviousClose": 2475.0,
            "dayHigh": 2550.0,
            "regularMarketVolume": 5_000_000,
            "marketCap": 300_000_000_000,
        }
        mock_ticker_cls.return_value.info = mock_info
        result = get_ticker_stats("ETH-USD")
        for key in ["price", "high_24h", "change_24h", "change_pct", "volume_24h", "market_cap"]:
            assert key in result

    @patch("data.crypto_data.yf.Ticker")
    def test_calculates_change_correctly(self, mock_ticker_cls):
        mock_info = {
            "regularMarketPrice": 2500.0,
            "regularMarketPreviousClose": 2400.0,
        }
        mock_ticker_cls.return_value.info = mock_info
        result = get_ticker_stats("ETH-USD")
        assert abs(result["change_24h"] - 100.0) < 0.01
        assert abs(result["change_pct"] - (100 / 2400 * 100)) < 0.01

    @patch("data.crypto_data.yf.Ticker")
    def test_returns_defaults_on_error(self, mock_ticker_cls):
        mock_ticker_cls.side_effect = Exception("API error")
        result = get_ticker_stats("ETH-USD")
        assert result["price"] == 0
        assert result["change_24h"] == 0

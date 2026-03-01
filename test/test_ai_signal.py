"""
Unit tests for data.ai_signal module.
Tests: generate_signals, _fallback_signals
"""

import pytest
import json
from unittest.mock import patch, MagicMock

from data.ai_signal import generate_signals, _fallback_signals


class TestFallbackSignals:
    def test_returns_two_signals(self):
        result = _fallback_signals("ETH-USD", 2000.0)
        assert len(result) == 2

    def test_first_signal_is_long(self):
        result = _fallback_signals("ETH-USD", 2000.0)
        assert result[0]["direction"] == "long"

    def test_second_signal_is_short(self):
        result = _fallback_signals("ETH-USD", 2000.0)
        assert result[1]["direction"] == "short"

    def test_signal_has_required_keys(self):
        result = _fallback_signals("ETH-USD", 2000.0)
        required = {"direction", "entry", "take_profit", "stop_loss", "style", "strategy", "time_ago"}
        for sig in result:
            assert required.issubset(sig.keys())

    def test_zero_price_uses_default(self):
        result = _fallback_signals("BTC-USD", 0)
        assert result[0]["entry"] > 0

    def test_negative_price_uses_default(self):
        result = _fallback_signals("BTC-USD", -100)
        assert result[0]["entry"] > 0

    def test_entry_close_to_current_price(self):
        price = 2000.0
        result = _fallback_signals("ETH-USD", price)
        for sig in result:
            assert abs(sig["entry"] - price) / price < 0.01

    def test_take_profit_and_stop_loss_make_sense_long(self):
        result = _fallback_signals("ETH-USD", 2000.0)
        long_sig = result[0]
        assert long_sig["take_profit"] > long_sig["entry"]
        assert long_sig["stop_loss"] < long_sig["entry"]

    def test_take_profit_and_stop_loss_make_sense_short(self):
        result = _fallback_signals("ETH-USD", 2000.0)
        short_sig = result[1]
        assert short_sig["take_profit"] < short_sig["entry"]
        assert short_sig["stop_loss"] > short_sig["entry"]


class TestGenerateSignals:
    @patch("data.ai_signal.get_client")
    def test_returns_signals_on_success(self, mock_get_client, sample_ohlcv_df):
        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.text = json.dumps([
            {"direction": "long", "entry": 1995.0, "take_profit": 2072.0,
             "stop_loss": 1966.0, "style": "Day", "strategy": "최대 수익"},
            {"direction": "short", "entry": 2010.0, "take_profit": 1940.0,
             "stop_loss": 2040.0, "style": "Swing", "strategy": "보수적"},
        ])
        mock_client.models.generate_content.return_value = mock_response
        mock_get_client.return_value = mock_client

        result = generate_signals("ETH-USD", sample_ohlcv_df, num_signals=2)
        assert len(result) == 2
        assert result[0]["direction"] in ("long", "short")

    @patch("data.ai_signal.get_client")
    def test_adds_time_ago_metadata(self, mock_get_client, sample_ohlcv_df):
        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.text = json.dumps([
            {"direction": "long", "entry": 2000.0, "take_profit": 2050.0, "stop_loss": 1980.0}
        ])
        mock_client.models.generate_content.return_value = mock_response
        mock_get_client.return_value = mock_client

        result = generate_signals("ETH-USD", sample_ohlcv_df, num_signals=1)
        assert "time_ago" in result[0]

    @patch("data.ai_signal.get_client")
    def test_handles_markdown_code_block_response(self, mock_get_client, sample_ohlcv_df):
        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.text = '```json\n[{"direction":"long","entry":2000,"take_profit":2050,"stop_loss":1980}]\n```'
        mock_client.models.generate_content.return_value = mock_response
        mock_get_client.return_value = mock_client

        result = generate_signals("ETH-USD", sample_ohlcv_df, num_signals=1)
        assert len(result) == 1

    @patch("data.ai_signal.get_client")
    def test_falls_back_on_api_error(self, mock_get_client, sample_ohlcv_df):
        mock_client = MagicMock()
        mock_client.models.generate_content.side_effect = Exception("API error")
        mock_get_client.return_value = mock_client

        result = generate_signals("ETH-USD", sample_ohlcv_df)
        assert len(result) == 2  # Fallback generates 2 signals

    def test_empty_df_returns_fallback(self, empty_df):
        result = generate_signals("ETH-USD", empty_df)
        assert len(result) == 2
        assert result[0]["entry"] > 0

"""
Unit tests for components.sidebar_copilot module.
Tests: _fallback_result, _try_parse_json
"""

import pytest
import json
from unittest.mock import patch, MagicMock

from components.sidebar_copilot import _fallback_result, _try_parse_json


class TestFallbackResult:
    def test_returns_dict(self):
        result = _fallback_result(2000.0)
        assert isinstance(result, dict)

    def test_long_when_rsi_below_50(self):
        result = _fallback_result(2000.0, rsi_val=30.0)
        assert result["direction"] == "long"

    def test_short_when_rsi_above_50(self):
        result = _fallback_result(2000.0, rsi_val=70.0)
        assert result["direction"] == "short"

    def test_has_all_required_keys(self):
        result = _fallback_result(2000.0, rsi_val=50.0)
        required = {"direction", "pattern", "rsi_analysis", "entry", "target", "stop_loss", "confidence", "reasoning"}
        assert required.issubset(result.keys())

    def test_includes_error_in_reasoning(self):
        result = _fallback_result(2000.0, rsi_val=50.0, error="test error")
        assert "test error" in result["reasoning"]

    def test_oversold_rsi_analysis(self):
        result = _fallback_result(2000.0, rsi_val=25.0)
        assert "과매도" in result["rsi_analysis"]

    def test_overbought_rsi_analysis(self):
        result = _fallback_result(2000.0, rsi_val=75.0)
        assert "과매수" in result["rsi_analysis"]

    def test_neutral_rsi_analysis(self):
        result = _fallback_result(2000.0, rsi_val=50.0)
        assert "중립" in result["rsi_analysis"]

    def test_none_rsi(self):
        result = _fallback_result(2000.0, rsi_val=None)
        assert result["rsi_analysis"] == "N/A"

    def test_confidence_is_low(self):
        result = _fallback_result(2000.0)
        assert result["confidence"] == "Low"


class TestTryParseJSON:
    def test_parses_clean_json(self):
        text = '{"direction":"long","entry":2000}'
        result = _try_parse_json(text, 2000.0)
        assert result["direction"] == "long"

    def test_parses_json_with_markdown_fences(self):
        text = '```json\n{"direction":"long","entry":2000}\n```'
        result = _try_parse_json(text, 2000.0)
        assert result["direction"] == "long"

    def test_extracts_json_from_text(self):
        text = 'Here is the result: {"direction":"short","entry":2100} Hope this helps!'
        result = _try_parse_json(text, 2000.0)
        assert result["direction"] == "short"

    def test_parses_json_wrapped_in_list(self):
        text = '[{"direction":"long","entry":2200}]'
        result = _try_parse_json(text, 2000.0)
        assert result["direction"] == "long"
        assert result["entry"] == 2200

    def test_falls_back_on_invalid(self):
        text = "This is not JSON at all"
        result = _try_parse_json(text, 2000.0)
        assert result["confidence"] == "Low"  # Fallback indicator

    def test_empty_string_falls_back(self):
        result = _try_parse_json("", 2000.0)
        assert "entry" in result

"""
Unit tests for data.gemini_config module.
Tests: get_client, get_auth_method, get_model_id
"""

import pytest
import os
from unittest.mock import patch, MagicMock


class TestGeminiConfig:
    def test_get_auth_method_returns_string(self):
        """get_auth_method should return a valid auth method string."""
        from data.gemini_config import get_auth_method
        result = get_auth_method()
        assert isinstance(result, str)
        assert result in ("vertex_ai", "api_key", "none")

    def test_get_model_id(self):
        """get_model_id should return a string."""
        from data.gemini_config import get_model_id
        result = get_model_id()
        assert isinstance(result, str)
        assert "gemini" in result

    @patch("google.genai.Client")
    @patch("google.auth.default")
    def test_get_client_vertex_ai(self, mock_auth_default, mock_client_cls):
        """Test getting client via Vertex AI path."""
        import data.gemini_config as gc
        gc._client = None  # Reset state
        
        mock_auth_default.return_value = (MagicMock(), "test-project")
        
        client = gc.get_client()
        
        assert gc._auth_method == "vertex_ai"
        assert client is not None
        mock_client_cls.assert_called_once()
        # Verify vertexai=True was passed
        kwargs = mock_client_cls.call_args.kwargs
        assert kwargs.get("vertexai") is True

    @patch("google.genai.Client")
    @patch.dict(os.environ, {"GEMINI_API_KEY": "test-key"})
    def test_get_client_api_key_fallback(self, mock_client_cls):
        """Test getting client via API key fallback path."""
        import data.gemini_config as gc
        gc._client = None
        
        # Mock auth to fail to trigger fallback
        with patch("google.auth.default", side_effect=Exception("No ADC")):
            client = gc.get_client()
            
        assert gc._auth_method == "api_key"
        assert client is not None
        mock_client_cls.assert_called_once()
        assert mock_client_cls.call_args.kwargs.get("api_key") == "test-key"

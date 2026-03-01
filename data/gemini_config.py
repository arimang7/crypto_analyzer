"""
Gemini Configuration — Central auth module using the new google-genai SDK.
Supports both Vertex AI (ADC/OAuth) and Google AI (API Key) through a unified Client.

Priority: Vertex AI (ADC) > Google AI (API Key)
"""

import os
from dotenv import load_dotenv
from google import genai

load_dotenv()

_client = None
_auth_method = "none"
_model_id = os.getenv("GEMINI_MODEL", "gemini-2.0-flash")


def get_client() -> genai.Client:
    """
    Initialize and return the GenAI Client.
    Tries Vertex AI (ADC) first, fallback to Google AI (API Key).
    """
    global _client, _auth_method

    if _client is not None:
        return _client

    # 1. Try Google AI (API Key) first
    api_key = os.getenv("GEMINI_API_KEY", "").strip()
    if api_key:
        _client = genai.Client(api_key=api_key)
        _auth_method = "api_key"
        print("[Gemini] 🔑 Managed via Google AI (API Key)")
        return _client

    # 2. Fallback to Vertex AI (ADC)
    try:
        # Check if we have some indicators of GCP environment or ADC
        import google.auth
        credentials, project = google.auth.default()
        
        # Even if credentials exist, genai.Client needs project/location for Vertex
        project_id = project or os.getenv("GOOGLE_CLOUD_PROJECT")
        location = os.getenv("VERTEX_LOCATION", "us-central1")

        _client = genai.Client(
            vertexai=True,
            project=project_id,
            location=location
        )
        _auth_method = "vertex_ai"
        print(f"[Gemini] ✅ Managed via Vertex AI — project={project_id}, location={location}")
        return _client
    except Exception as e:
        print(f"[Gemini] ℹ️ Vertex AI not available or ADC missing: {e}")

    print("[Gemini] ⚠️ No authentication configured!")
    # Create a dummy client to avoid None pointer errors elsewhere, 
    # but it will fail on actual calls.
    return None


def get_model_id() -> str:
    """Return the configured model ID."""
    return _model_id


def get_auth_method() -> str:
    """Return current auth method: 'vertex_ai', 'api_key', or 'none'."""
    return _auth_method


# Initialize on import
get_client()

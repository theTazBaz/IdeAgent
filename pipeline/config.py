"""
pipeline/config.py
==================
Loads all environment variables and defines shared constants.
Values are lazy-checked at point of use so missing keys produce clear errors.
"""
import os
from typing import Optional
from dotenv import load_dotenv

load_dotenv()

# ------------------------------------------------------------------
# Database
# ------------------------------------------------------------------
DATABASE_URL: Optional[str] = os.environ.get("DATABASE_URL")

# ------------------------------------------------------------------
# External API keys
# ------------------------------------------------------------------
TMDB_API_KEY: Optional[str] = os.environ.get("TMDB_API_KEY")
SPOTIFY_CLIENT_ID: Optional[str] = os.environ.get("SPOTIFY_CLIENT_ID")
SPOTIFY_CLIENT_SECRET: Optional[str] = os.environ.get("SPOTIFY_CLIENT_SECRET")
GEMINI_API_KEY: Optional[str] = os.environ.get("GEMINI_API_KEY")

# ------------------------------------------------------------------
# Model settings
# ------------------------------------------------------------------
EMBED_MODEL: str = "nomic-ai/nomic-embed-text-v1.5"   # runs locally, no API key
EMBED_DIM: int = 768                                    # must match schema vector(768)
LLM_MODEL: str = "qwen/qwen3.6-27b"                    # Groq model for synthesis

# ------------------------------------------------------------------
# Helpers
# ------------------------------------------------------------------
def require(var_name: str, value: Optional[str], hint: str = "") -> str:
    """Raise a clear EnvironmentError if a required env var is missing."""
    if not value:
        msg = f"\n\n  ❌  {var_name} is not set in your .env file."
        if hint:
            msg += f"\n     {hint}"
        raise EnvironmentError(msg)
    return value

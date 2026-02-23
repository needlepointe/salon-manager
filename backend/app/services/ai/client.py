"""Anthropic SDK singleton — imported by all AI service modules."""
import anthropic
from app.config import get_settings

settings = get_settings()

# Single shared client — thread-safe, reuses HTTP connections
anthropic_client = anthropic.Anthropic(api_key=settings.anthropic_api_key)

MODEL = "claude-opus-4-6"

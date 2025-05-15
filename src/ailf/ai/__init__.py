"""
AILF AI Module.

This module provides a comprehensive interface for AI and LLM interactions.

Key Components:
    AIEngine: Main class providing AI/LLM interaction interface
    AIEngineError: Base exception class for AI engine errors
"""

from .engine import (
    AIEngine,
    AIEngineError,
    ModelError,
    ContentFilterError,
    GeminiHarmCategory,
    GeminiThreshold,
    default_gemini_settings,
    default_openai_settings,
    default_anthropic_settings,
    create_default_safety_settings,
)

__all__ = [
    "AIEngine",
    "AIEngineError",
    "ModelError",
    "ContentFilterError",
    "GeminiHarmCategory",
    "GeminiThreshold",
    "default_gemini_settings",
    "default_openai_settings",
    "default_anthropic_settings",
    "create_default_safety_settings",
]
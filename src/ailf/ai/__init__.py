"""AI-related utilities, including the AI engine and tools."""
from . import engine
from .engine import AIEngine, AIEngineError
from .engine_factory import create_ai_engine
try:
    from .openai_engine import OpenAIEngine
except ImportError:
    # OpenAI may not be installed
    pass
    
try:
    from .anthropic_engine import AnthropicEngine
except ImportError:
    # Anthropic may not be installed
    pass

# tools will be imported from the tools subdirectory if it's created

__all__ = [
    "engine",
    "AIEngine",
    "AIEngineError",
    "create_ai_engine",
    "OpenAIEngine",
    "AnthropicEngine"
]

"""Schema models for the AILF package.

This package contains Pydantic models that define data structures used throughout
the AILF toolkit, ensuring type safety and data validation.
"""

# Import schemas for convenient access
from .ai import (
    AIResponse, AIRequest, AIEngineConfig, GeminiSettings, 
    AnthropicSettings, OpenAISettings, GeminiSafetySettings
)
from .redis import RedisConfig
from .zmq_devices import DeviceType, DeviceConfig, AuthConfig
from .cognition import ReActStep, ReActState, Plan, PlanStep, IntentRefinementRequest, IntentRefinementResponse
from .tree_of_thought import ThoughtNode, ThoughtState, ToTConfiguration, ToTState, ToTResult, EvaluationStrategy
from .prompt_engineering import PromptTemplateV1, PromptLibraryConfig, PromptVariable, PromptMetadata

# Import the feedback models. To avoid circular imports, we're using import statements 
# that will be executed when the symbols are first accessed
import importlib

# Create dynamic imports to avoid circular references
def __getattr__(name):
    """Dynamically import feedback models to avoid circular imports."""
    if name in ('LoggedInteraction'):
        module = importlib.import_module('ailf.schemas.feedback.models')
        return getattr(module, name)
    elif name in ('PerformanceMetric', 'PerformanceReport', 'LearningEvent'):
        module = importlib.import_module('ailf.schemas.feedback')
        return getattr(module, name)
    raise AttributeError(f"module {__name__} has no attribute {name}")

__all__ = [
    # AI schemas
    "AIResponse", "AIRequest", "AIEngineConfig", "GeminiSettings", 
    "AnthropicSettings", "OpenAISettings", "GeminiSafetySettings",
    
    # Tree of Thought schemas
    "ThoughtNode", "ThoughtState", "ToTConfiguration", "ToTState", "ToTResult", "EvaluationStrategy",
    
    # Prompt Engineering schemas
    "PromptTemplateV1", "PromptLibraryConfig", "PromptVariable", "PromptMetadata",
    
    # Redis schemas
    "RedisConfig",
    
    # ZMQ schemas
    "DeviceType",
    "DeviceConfig",
    "AuthConfig",
    
    # Cognition schemas
    "ReActStep",
    "ReActState",
    "Plan",
    "PlanStep",
    "IntentRefinementRequest",
    "IntentRefinementResponse",
    
    # Feedback schemas
    "LoggedInteraction",
    "PerformanceMetric",
    "PerformanceReport",
    "LearningEvent",
]

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
from .feedback import LoggedInteraction, PerformanceMetric, PerformanceReport, LearningEvent
from .tree_of_thought import ThoughtNode, ThoughtState, ToTConfiguration, ToTState, ToTResult, EvaluationStrategy
from .prompt_engineering import PromptTemplateV1, PromptLibraryConfig, PromptVariable, PromptMetadata

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
    "PromptTemplateV1",
    "PromptLibrary",
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

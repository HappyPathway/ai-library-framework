"""
AILF Cognition Module.

This module provides cognitive capabilities for AI agents, including:
- ReAct reasoning (Reason-Action-Observation loops)
- Task planning and decomposition
- Intent refinement and clarification
- Prompt templating and management
"""

from ailf.schemas.cognition import (
    # Schema classes
    ReActStep, ReActState, ReActStepType,
    PlanStep, Plan,
    IntentRefinementRequest, IntentRefinementResponse,
    PromptTemplateV1, PromptLibrary,
    TaskContext, ProcessingResult,
    
    # Implementation classes
    ReActProcessor, TaskPlanner, IntentRefiner
)

__all__ = [
    # Schema classes
    'ReActStep', 'ReActState', 'ReActStepType',
    'PlanStep', 'Plan',
    'IntentRefinementRequest', 'IntentRefinementResponse', 
    'PromptTemplateV1', 'PromptLibrary',
    'TaskContext', 'ProcessingResult',
    
    # Implementation classes
    'ReActProcessor', 'TaskPlanner', 'IntentRefiner'
]

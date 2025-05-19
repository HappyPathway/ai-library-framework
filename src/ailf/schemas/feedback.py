"""
Schemas for feedback and interaction logging in the AILF framework.

This module contains Pydantic models for interaction logging, performance analysis,
and adaptive learning components of the feedback system.
"""

import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class LoggedInteraction(BaseModel):
    """
    Represents a logged interaction with an AI agent or system.
    This schema is designed to capture comprehensive details about an interaction
    for analysis, debugging, and adaptive learning purposes.
    """
    interaction_id: uuid.UUID = Field(default_factory=uuid.uuid4, description="Unique identifier for this interaction log entry.")
    session_id: Optional[str] = Field(None, description="Identifier for the session this interaction belongs to.")
    user_id: Optional[str] = Field(None, description="Identifier for the user involved in the interaction.")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Timestamp of when the interaction was logged (UTC).")

    # Input and Prompt Details
    input_summary: Optional[str] = Field(None, description="A brief summary or type of the input provided.")
    input_payload: Optional[Any] = Field(None, description="The actual input payload, if feasible to store.")
    prompt_template_id: Optional[str] = Field(None, description="Unique identifier of the prompt template used, if any.")
    prompt_template_version: Optional[str] = Field(None, description="Version of the prompt template used.")
    rendered_prompt: Optional[str] = Field(None, description="The fully rendered prompt text sent to the LLM.")

    # LLM and Agent Action Details
    llm_model_used: Optional[str] = Field(None, description="Identifier of the LLM model used for this interaction.")
    llm_response_summary: Optional[str] = Field(None, description="A brief summary or type of the LLM's direct response.")
    llm_response_payload: Optional[Any] = Field(None, description="The actual payload received from the LLM, if feasible.")
    agent_actions: Optional[List[Dict[str, Any]]] = Field(default_factory=list, description="Structured list of actions taken by the agent.")

    # Output Details
    final_agent_output_summary: Optional[str] = Field(None, description="A brief summary or type of the final output provided to the user/system.")
    final_agent_output_payload: Optional[Any] = Field(None, description="The actual final output payload, if feasible.")

    # Feedback and Error Details
    user_feedback_score: Optional[float] = Field(None, description="Explicit user feedback score (e.g., 1-5, -1/0/1).")
    user_feedback_text: Optional[str] = Field(None, description="Explicit user feedback text.")
    error_message: Optional[str] = Field(None, description="Error message if an error occurred during the interaction.")
    error_traceback: Optional[str] = Field(None, description="Full traceback if an error occurred.")

    # Metrics and Tags
    performance_metrics: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Key-value store for performance metrics (e.g., latency_ms, tokens_used).")
    tags: Optional[List[str]] = Field(default_factory=list, description="List of tags for categorizing or filtering interactions.")
    metadata: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Any other relevant metadata.")

    class Config:
        validate_assignment = True
        extra = "forbid"


class PerformanceMetric(BaseModel):
    """Schema for a single performance metric."""
    
    metric_id: str = Field(
        ...,
        description="Unique identifier for this metric."
    )
    name: str = Field(
        ...,
        description="Human-readable name of the metric."
    )
    value: float = Field(
        ...,
        description="The value of the metric."
    )
    timestamp: datetime = Field(
        default_factory=datetime.utcnow,
        description="When the metric was recorded."
    )
    context: Dict[str, Any] = Field(
        default_factory=dict,
        description="Contextual information about this metric measurement."
    )


class PerformanceReport(BaseModel):
    """Schema for a collection of performance metrics."""
    
    report_id: str = Field(
        ...,
        description="Unique identifier for this report."
    )
    agent_id: str = Field(
        ...,
        description="Identifier of the agent being analyzed."
    )
    metrics: List[PerformanceMetric] = Field(
        default_factory=list,
        description="List of performance metrics."
    )
    start_time: datetime = Field(
        ...,
        description="Start of the time period covered by this report."
    )
    end_time: datetime = Field(
        default_factory=datetime.utcnow,
        description="End of the time period covered by this report."
    )
    summary: Dict[str, Any] = Field(
        default_factory=dict,
        description="Summary statistics and analysis of the metrics."
    )


class LearningEvent(BaseModel):
    """Schema for an adaptive learning event."""
    
    event_id: str = Field(
        ...,
        description="Unique identifier for this learning event."
    )
    agent_id: str = Field(
        ...,
        description="Identifier of the agent involved in the learning event."
    )
    event_type: str = Field(
        ...,
        description="Type of learning event (e.g., 'parameter_update', 'model_refresh')."
    )
    timestamp: datetime = Field(
        default_factory=datetime.utcnow,
        description="When the learning event occurred."
    )
    changes: Dict[str, Any] = Field(
        default_factory=dict,
        description="Changes made during this learning event."
    )
    reason: Optional[str] = Field(
        None,
        description="Reason for the learning event or changes."
    )
    performance_before: Optional[Dict[str, float]] = Field(
        None,
        description="Performance metrics before the changes."
    )
    performance_after: Optional[Dict[str, float]] = Field(
        None,
        description="Performance metrics after the changes."
    )

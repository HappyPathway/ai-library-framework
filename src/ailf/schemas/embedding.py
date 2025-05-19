"""OpenAI Embeddings API entity schemas.

This module provides Pydantic models for OpenAI Embeddings API entities.
"""
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class Embedding(BaseModel):
    """A single embedding vector."""
    object: str
    embedding: List[float]
    index: int


class CreateEmbeddingResponse(BaseModel):
    """Response from the Embeddings API."""
    object: str
    data: List[Embedding]
    model: str
    usage: Dict[str, int]


class EmbeddingUsage(BaseModel):
    """Usage statistics for embedding requests."""
    prompt_tokens: int
    total_tokens: int

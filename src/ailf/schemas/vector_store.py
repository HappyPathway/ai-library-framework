"""Vector Store API entity schemas.

This module provides Pydantic models for Vector Store API entities.
"""
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class VectorStore(BaseModel):
    """A vector store for semantic search."""
    id: str
    object: str = "vector_store"
    created_at: int
    name: Optional[str] = None
    description: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)


class VectorStoreSearchResult(BaseModel):
    """A single search result from a vector store."""
    id: str
    score: float
    text: str
    metadata: Dict[str, Any] = Field(default_factory=dict)
    file_id: Optional[str] = None


class VectorStoreSearchResponse(BaseModel):
    """Response from a vector store search."""
    object: str = "vector_store.search_results"
    data: List[VectorStoreSearchResult]


class VectorStoreFile(BaseModel):
    """A file in a vector store."""
    id: str
    object: str = "vector_store.file"
    created_at: int
    vector_store_id: str
    filename: str
    purpose: str
    bytes: int
    status: str
    status_details: Optional[str] = None
    metadata: Dict[str, str] = Field(default_factory=dict)


class VectorStoreDeleted(BaseModel):
    """Response when a vector store is deleted."""
    id: str
    object: str = "vector_store.deleted"
    deleted: bool = True

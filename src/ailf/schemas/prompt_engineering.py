"""Prompt Engineering schema models.

This module provides Pydantic models for prompt templates and prompt library
configurations that enable structured prompt management and optimization.
"""

from enum import Enum
from typing import Dict, List, Optional, Union, Any
from pydantic import BaseModel, Field


class PromptVariable(BaseModel):
    """Definition of a variable in a prompt template.
    
    Attributes:
        name: The variable name
        description: Description of the variable
        default_value: Optional default value
        required: Whether this variable is required
    """
    
    name: str
    description: str = ""
    default_value: Optional[str] = None
    required: bool = True


class PromptMetadata(BaseModel):
    """Metadata for a prompt template.
    
    Attributes:
        author: Author of the prompt template
        version: Version of the template
        description: Description of the template
        use_case: Intended use case for this template
        tags: List of tags for categorization
        performance_metrics: Performance metrics associated with this template
    """
    
    author: Optional[str] = None
    version: str = "1.0.0"
    description: str = ""
    use_case: Optional[str] = None
    tags: List[str] = []
    performance_metrics: Optional[Dict[str, float]] = None


class PromptTemplateVersion(BaseModel):
    """A specific version of a prompt template.
    
    Attributes:
        id: Unique identifier for this version
        template: The prompt template text
        variables: Dictionary of variable definitions
        metadata: Metadata for this version
        created_at: Timestamp when this version was created
    """
    
    id: str
    template: str
    variables: Dict[str, PromptVariable] = {}
    metadata: PromptMetadata = PromptMetadata()
    created_at: Optional[str] = None


class PromptTemplateV1(BaseModel):
    """A versioned prompt template with variables.
    
    Attributes:
        id: Unique identifier for this template
        name: Name of the template
        current_version: The current active version
        versions: All versions of this template
        variables: Dictionary of variable definitions (for the current version)
        metadata: Metadata for the current version
        template: The current version's template text
    """
    
    id: str
    name: str
    current_version: str
    versions: Dict[str, PromptTemplateVersion] = {}
    variables: Dict[str, PromptVariable] = {}
    metadata: PromptMetadata = PromptMetadata()
    template: str = ""
    
    class Config:
        """Pydantic configuration."""
        
        validate_assignment = True


class StorageBackend(str, Enum):
    """Storage backend options for the prompt library."""
    
    LOCAL_FILE = "local_file"
    GCS = "gcs"
    S3 = "s3"
    DATABASE = "database"
    MEMORY = "memory"


class PromptLibraryConfig(BaseModel):
    """Configuration for the prompt library.
    
    Attributes:
        storage_backend: Which backend to use for storing prompts
        storage_path: Path or connection string for the storage
        auto_version: Whether to automatically version prompts
        enable_metrics: Whether to collect metrics on prompt usage
        default_author: Default author for new prompts
    """
    
    storage_backend: StorageBackend = StorageBackend.MEMORY
    storage_path: Optional[str] = None
    auto_version: bool = True
    enable_metrics: bool = False
    default_author: Optional[str] = None


__all__ = [
    "PromptVariable",
    "PromptMetadata", 
    "PromptTemplateVersion",
    "PromptTemplateV1",
    "StorageBackend",
    "PromptLibraryConfig"
]

"""
Schema translation utilities for AILF-Kagent integration.

This module provides functions for translating between AILF's Pydantic models
and Kagent's schema definitions, enabling seamless data exchange.
"""

from typing import Any, Dict, List, Optional, Type, Union, get_origin, get_args
import inspect
from pydantic import BaseModel, Field, create_model


def map_ailf_to_kagent_schema(
    ailf_schema: Type[BaseModel]
) -> Type[BaseModel]:
    """Convert an AILF Pydantic model to a Kagent-compatible schema.
    
    Args:
        ailf_schema: The AILF Pydantic model to convert
        
    Returns:
        A new Pydantic model compatible with Kagent's expectations
        
    Raises:
        ValueError: If the provided schema is not a valid Pydantic model
    """
    if not (inspect.isclass(ailf_schema) and issubclass(ailf_schema, BaseModel)):
        raise ValueError("Input must be a Pydantic BaseModel")
    
    # Extract field information from the AILF schema
    fields = {}
    for name, field in ailf_schema.model_fields.items():
        # Include all relevant field metadata
        fields[name] = (
            field.annotation,
            Field(
                default=field.default,
                description=field.description,
                title=field.title,
                examples=field.examples
            )
        )
    
    # Create a new model with Kagent compatibility in mind
    kagent_model = create_model(
        f"Kagent{ailf_schema.__name__}",
        **fields,
        __doc__=ailf_schema.__doc__
    )
    
    return kagent_model


def map_kagent_to_ailf_schema(
    kagent_schema: Type[BaseModel]
) -> Type[BaseModel]:
    """Convert a Kagent schema to an AILF-compatible Pydantic model.
    
    Args:
        kagent_schema: The Kagent schema to convert
        
    Returns:
        A new Pydantic model compatible with AILF's expectations
        
    Raises:
        ValueError: If the provided schema is not a valid Pydantic model
    """
    if not (inspect.isclass(kagent_schema) and issubclass(kagent_schema, BaseModel)):
        raise ValueError("Input must be a Pydantic BaseModel")
    
    # Extract field information from the Kagent schema
    fields = {}
    for name, field in kagent_schema.model_fields.items():
        # Include all relevant field metadata
        fields[name] = (
            field.annotation,
            Field(
                default=field.default,
                description=field.description,
                title=field.title,
                examples=field.examples
            )
        )
    
    # Create a new model with AILF compatibility in mind
    ailf_model = create_model(
        f"AILF{kagent_schema.__name__}",
        **fields,
        __doc__=kagent_schema.__doc__
    )
    
    return ailf_model


def convert_instance_to_schema(
    instance: Any,
    target_schema: Type[BaseModel]
) -> BaseModel:
    """Convert an instance to conform to a target schema.
    
    Args:
        instance: The instance to convert (either dict or BaseModel)
        target_schema: The target schema to convert to
        
    Returns:
        A new instance conforming to the target schema
        
    Raises:
        ValueError: If the conversion fails
    """
    # Convert to dict if it's a BaseModel
    instance_dict = instance.model_dump() if isinstance(instance, BaseModel) else instance
    
    # Create an instance of the target schema
    try:
        return target_schema.model_validate(instance_dict)
    except Exception as e:
        raise ValueError(f"Failed to convert instance to {target_schema.__name__}: {str(e)}")


class SchemaRegistry:
    """Registry for managing schema mappings between AILF and Kagent.
    
    This registry manages known schema translations between the two frameworks,
    enabling automatic conversion where possible.
    
    Attributes:
        _ailf_to_kagent: Dictionary mapping AILF schema types to Kagent schema types
        _kagent_to_ailf: Dictionary mapping Kagent schema types to AILF schema types
    """
    
    def __init__(self):
        """Initialize an empty schema registry."""
        self._ailf_to_kagent = {}
        self._kagent_to_ailf = {}
    
    def register_mapping(
        self,
        ailf_schema: Type[BaseModel],
        kagent_schema: Type[BaseModel]
    ) -> None:
        """Register a bidirectional mapping between AILF and Kagent schemas.
        
        Args:
            ailf_schema: The AILF schema type
            kagent_schema: The corresponding Kagent schema type
        """
        self._ailf_to_kagent[ailf_schema] = kagent_schema
        self._kagent_to_ailf[kagent_schema] = ailf_schema
    
    def get_kagent_schema(
        self,
        ailf_schema: Type[BaseModel]
    ) -> Optional[Type[BaseModel]]:
        """Get the corresponding Kagent schema for an AILF schema.
        
        Args:
            ailf_schema: The AILF schema to look up
            
        Returns:
            The corresponding Kagent schema, or None if not found
        """
        return self._ailf_to_kagent.get(ailf_schema)
    
    def get_ailf_schema(
        self,
        kagent_schema: Type[BaseModel]
    ) -> Optional[Type[BaseModel]]:
        """Get the corresponding AILF schema for a Kagent schema.
        
        Args:
            kagent_schema: The Kagent schema to look up
            
        Returns:
            The corresponding AILF schema, or None if not found
        """
        return self._kagent_to_ailf.get(kagent_schema)
    
    def convert_to_kagent(
        self,
        instance: Union[Dict, BaseModel]
    ) -> BaseModel:
        """Convert an AILF instance to its Kagent equivalent.
        
        Args:
            instance: The AILF instance to convert
            
        Returns:
            The converted Kagent instance
            
        Raises:
            ValueError: If no mapping exists for the instance type
        """
        if isinstance(instance, dict):
            raise ValueError("Cannot determine schema type from dictionary")
        
        ailf_type = type(instance)
        kagent_type = self.get_kagent_schema(ailf_type)
        
        if not kagent_type:
            raise ValueError(f"No registered mapping for AILF type {ailf_type.__name__}")
        
        return convert_instance_to_schema(instance, kagent_type)
    
    def convert_to_ailf(
        self,
        instance: Union[Dict, BaseModel]
    ) -> BaseModel:
        """Convert a Kagent instance to its AILF equivalent.
        
        Args:
            instance: The Kagent instance to convert
            
        Returns:
            The converted AILF instance
            
        Raises:
            ValueError: If no mapping exists for the instance type
        """
        if isinstance(instance, dict):
            raise ValueError("Cannot determine schema type from dictionary")
        
        kagent_type = type(instance)
        ailf_type = self.get_ailf_schema(kagent_type)
        
        if not ailf_type:
            raise ValueError(f"No registered mapping for Kagent type {kagent_type.__name__}")
        
        return convert_instance_to_schema(instance, ailf_type)

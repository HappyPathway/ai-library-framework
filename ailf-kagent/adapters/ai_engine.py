"""
Adapter for connecting AILF's placeholder AIEngine to Kagent's model capabilities.

This module provides an implementation of AIEngine that uses Kagent's model
access to provide actual AI reasoning capabilities for AILF components.
"""

from typing import Any, Dict, List, Optional, Type, Union
from pydantic import BaseModel

import kagent.core
from kagent.schema import AgentResponse, AgentMessage

# Try importing the placeholder AIEngine to ensure our implementation matches the expected interface
try:
    from utils.ai.engine import AIEngine as OriginalAIEngine
    class AIEngineAdapter(OriginalAIEngine):
        """Adapter that implements AILF's AIEngine interface using Kagent's model access."""
        pass
except ImportError:
    # If the original AIEngine isn't available, create a base implementation
    # that matches what AILF components expect
    class AIEngineAdapter:
        """
        Implementation of AIEngine that uses Kagent's model capabilities.
        
        This adapter allows AILF components that rely on AIEngine (like ReActProcessor,
        ReflectionEngine, etc.) to work properly by delegating to Kagent's language models.
        """

        def __init__(
            self, 
            model_name: str = "gpt-4-turbo", 
            feature_name: str = "ailf_adapter",
            **kwargs
        ):
            """
            Initialize the AIEngine adapter.
            
            Args:
                model_name: The name of the model to use
                feature_name: The feature name for logging/monitoring
                kwargs: Additional configuration options
            """
            self.model_name = model_name
            self.feature_name = feature_name
            self.config = kwargs
            self._initialize()
            
        def _initialize(self):
            """Initialize the Kagent model access."""
            # Import here to avoid circular imports
            from kagent.core.llm import LLMClient
            self.llm_client = LLMClient(model=self.model_name)
            
        async def analyze(
            self, 
            content: str, 
            output_schema: Type[BaseModel],
            system_prompt: Optional[str] = None
        ) -> BaseModel:
            """
            Analyze content and return structured output matching the schema.
            
            This is the primary method used by AILF components like ReActProcessor
            and ReflectionEngine.
            
            Args:
                content: The content to analyze
                output_schema: The Pydantic schema for the output
                system_prompt: Optional system prompt for the model
                
            Returns:
                A Pydantic model instance of the specified output_schema
            """
            messages = []
            
            if system_prompt:
                messages.append({"role": "system", "content": system_prompt})
                
            messages.append({"role": "user", "content": content})
            
            # Convert the schema to JSON schema format
            json_schema = output_schema.model_json_schema()
            
            # Generate a response with structured output
            response = await self.llm_client.generate_structured_output(
                messages=messages,
                schema=json_schema,
                model=self.model_name
            )
            
            # Convert the response to the specified schema
            return output_schema.model_validate(response)
            
        async def generate(
            self,
            prompt: str,
            output_schema: Optional[Type[BaseModel]] = None,
            system_prompt: Optional[str] = None,
            **kwargs
        ) -> Union[str, BaseModel]:
            """
            Generate a response from the AI model.
            
            Args:
                prompt: The prompt to send to the model
                output_schema: Optional schema for structured output
                system_prompt: Optional system prompt
                kwargs: Additional generation parameters
                
            Returns:
                Either a string response or a structured output based on output_schema
            """
            if output_schema:
                return await self.analyze(prompt, output_schema, system_prompt)
                
            # For unstructured output
            messages = []
            
            if system_prompt:
                messages.append({"role": "system", "content": system_prompt})
                
            messages.append({"role": "user", "content": prompt})
            
            # Generate a simple text response
            response = await self.llm_client.generate(
                messages=messages,
                model=self.model_name,
                **kwargs
            )
            
            return response.content

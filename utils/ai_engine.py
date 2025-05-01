"""Unified AI Engine with LLM Interactions

This module provides a comprehensive interface for AI and LLM interactions,
combining the best features of both the AIEngine and BaseLLMAgent approaches.
It supports both structured and unstructured outputs, with robust monitoring,
error handling, and type safety.

Features:
- Multiple model support (OpenAI, Gemini, etc.)
- Structured output using Pydantic models
- Comprehensive monitoring and logging
- Error handling and retries
- Type-safe interactions
- Tool registration for agents

Example:
    ```python
    from utils.ai_engine import AIEngine
    from my_schemas import JobAnalysis
    
    # Create an engine instance
    engine = AIEngine(
        feature_name='job_analysis',
        output_type=JobAnalysis
    )
    
    # Generate structured output
    result = await engine.generate(
        prompt="Analyze this job description...",
        output_type=JobAnalysis
    )
    
    # Generate free text
    text = await engine.generate_text(
        prompt="Write a cover letter..."
    )
    
    # Use as an agent with tools
    @engine.add_tool
    async def search_jobs(query: str) -> List[dict]:
        # Tool implementation
        pass
    ```
"""

import os
import asyncio
from typing import Any, Dict, Generic, List, Optional, Type, TypeVar, Union
from pydantic import BaseModel
from pydantic_ai import Agent, RunContext, Prompt
from pydantic_ai.exceptions import ModelRetry, UnexpectedModelBehavior
from pydantic_ai.usage import UsageLimits
from pydantic_ai.monitoring import LogfireMonitoring

from .logging import setup_logging
from .monitoring import setup_monitoring
from .secrets import secret_manager

# Initialize logging and monitoring
logger = setup_logging('ai_engine')
monitoring = setup_monitoring('ai_engine')

# Type variable for output types
T = TypeVar('T')

class AIEngine(Generic[T]):
    """Unified AI Engine for all AI/LLM interactions.
    
    This class combines the functionality of both AIEngine and BaseLLMAgent,
    providing a single interface for all AI interactions. It supports:
    - Multiple model providers (OpenAI, Gemini, etc.)
    - Structured and unstructured output
    - Tool registration for agent functionality
    - Comprehensive monitoring and error handling
    """
    
    def __init__(
        self,
        feature_name: str,
        output_type: Optional[Type[BaseModel]] = None,
        model_name: str = 'openai:gpt-4-turbo',
        provider: str = 'openai',
        instructions: Optional[str] = None,
        retries: int = 2
    ):
        """Initialize the AI engine.
        
        Args:
            feature_name: Name of the feature using this engine
            output_type: Optional Pydantic model for structured output
            model_name: Name of the model to use
            provider: AI provider to use ('openai' or 'gemini')
            instructions: Optional system instructions
            retries: Number of retries for failed generations
        """
        self.feature_name = feature_name
        self.output_type = output_type
        self.model_name = model_name
        self.provider = provider
        self.instructions = instructions
        self.retries = retries
        
        # Set up monitoring for this feature
        self.monitoring = setup_monitoring(f'ai_{feature_name}')
        
        # Configure monitoring with Logfire
        self.logfire = LogfireMonitoring(
            project_id="jobsearch-ai",
            environment=os.getenv("ENVIRONMENT", "development"),
            service_name=feature_name
        )
        
        # Initialize the agent
        self._setup_agent()
        
    def _setup_agent(self) -> None:
        """Configure and initialize the AI agent."""
        try:
            self.monitoring.increment('setup_agent')
            
            # Get appropriate API key
            if self.provider == 'openai':
                api_key = secret_manager.get_secret('OPENAI_API_KEY')
            else:  # gemini
                api_key = secret_manager.get_secret('GEMINI_API_KEY')
                
            if not api_key:
                raise ValueError(f"Could not retrieve {self.provider} API key")
            
            # Create the agent with configuration
            self.agent = Agent(
                self.model_name,
                output_type=self.output_type,
                deps_type=None,
                instructions=self.instructions,
                retries=self.retries,
                monitoring=self.logfire,
                api_key=api_key
            )
            
            self.monitoring.track_success('setup_agent')
            logger.info(f"Agent for {self.feature_name} initialized successfully")
            
        except Exception as e:
            self.monitoring.track_error('setup_agent', str(e))
            logger.error(f"Error setting up agent: {str(e)}")
            raise
            
    async def generate(
        self,
        prompt: str,
        output_type: Optional[Type[BaseModel]] = None,
        model_settings: Optional[Dict[str, Any]] = None,
        usage_limits: Optional[UsageLimits] = None,
        message_history: Optional[list] = None,
        example_data: Optional[Dict[str, Any]] = None,
        max_retries: Optional[int] = None
    ) -> Any:
        """Generate content with the AI model.
        
        Args:
            prompt: Input prompt for the model
            output_type: Override the default output type
            model_settings: Optional model configuration
            usage_limits: Optional token usage limits
            message_history: Optional conversation history
            example_data: Optional example output format
            max_retries: Override default retry count
            
        Returns:
            Generated content of the specified type
        """
        final_output_type = output_type or self.output_type
        metric_name = f"generate_{self.feature_name}"
        retries = max_retries or self.retries
        
        try:
            self.monitoring.increment(metric_name)
            logger.info(f"Generating response with {self.model_name}")
            
            # Enhance prompt with example if provided
            if example_data and final_output_type:
                prompt = f"{prompt}\n\nExpected output format:\n{example_data}"
            
            # Run generation with monitoring
            result = await self.agent.run(
                user_prompt=prompt,
                output_type=final_output_type,
                model_settings=model_settings,
                usage_limits=usage_limits,
                message_history=message_history
            )
            
            # Track usage
            usage = result.usage()
            self.monitoring.track_tokens(
                feature=self.feature_name,
                request_tokens=usage.request_tokens,
                response_tokens=usage.response_tokens,
                model=self.model_name
            )
            
            self.monitoring.track_success(metric_name)
            return result.output
            
        except Exception as e:
            self.monitoring.track_error(metric_name, str(e))
            logger.error(f"Error during generation: {str(e)}")
            raise
            
    async def generate_text(
        self,
        prompt: str,
        max_length: Optional[int] = None,
        **kwargs
    ) -> Optional[str]:
        """Generate unstructured text content.
        
        Args:
            prompt: Input prompt
            max_length: Optional maximum length
            **kwargs: Additional arguments for generate()
            
        Returns:
            Generated text or None on failure
        """
        try:
            # Use str as output type for unstructured text
            result = await self.generate(
                prompt=prompt,
                output_type=str,
                model_settings={'max_length': max_length} if max_length else None,
                **kwargs
            )
            return result
        except Exception as e:
            logger.error(f"Error generating text: {str(e)}")
            return None
            
    def add_tool(
        self,
        func: callable,
        name: Optional[str] = None,
        description: Optional[str] = None,
        retries: Optional[int] = None
    ) -> callable:
        """Register a tool function with the agent.
        
        Args:
            func: Function to register as a tool
            name: Optional custom name
            description: Optional description
            retries: Optional retry count
            
        Returns:
            Decorated function
        """
        return self.agent.tool(
            name=name,
            description=description,
            retries=retries or self.retries
        )(func)
        
    def add_system_prompt(self, func: callable) -> callable:
        """Register a system prompt function.
        
        Args:
            func: Function that returns system prompt
            
        Returns:
            Decorated function
        """
        return self.agent.system_prompt(func)
    
    def run_sync(
        self,
        prompt: str,
        **kwargs
    ) -> Any:
        """Run generation synchronously.
        
        Args:
            prompt: Input prompt
            **kwargs: Additional arguments
            
        Returns:
            Generated content
        """
        result = self.agent.run_sync(prompt, **kwargs)
        return result.output

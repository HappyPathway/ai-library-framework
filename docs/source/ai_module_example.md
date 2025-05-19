# AI Module Structure

This document demonstrates how the AI engine module is structured in the AILF framework.

## Current Structure

The AI-related code is organized in a logical structure in the src-based layout:

```
/src/ailf/
  ├── ai_engine.py          # Main AI engine implementation (legacy, being migrated)
  ├── ai/                   # AI module directory
  │   ├── __init__.py       # Exports key functionality
  │   ├── engine.py         # Enhanced AI engine for model interactions
  │   ├── providers/        # Provider-specific implementations
  │   │   ├── __init__.py
  │   │   ├── openai.py     # OpenAI-specific functionality
  │   │   ├── gemini.py     # Google Gemini models integration
  │   │   └── anthropic.py  # Anthropic Claude models integration
  │   └── tools/            # AI tools implementation
  │       ├── __init__.py
  │       ├── search.py     # Search tool implementation
  │       └── analysis.py   # Analysis tool implementation
  └── schemas/              # Schema definitions
      ├── __init__.py       # Exports key schemas
      └── ai.py             # AI-related schemas
```

## Implementation Example

### `/src/ailf/schemas/ai.py`

```python
"""AI-related schemas.

This module contains schemas used by the AI engine components.
"""
from typing import Dict, List, Optional, Union, Literal
from pydantic import BaseModel, Field

class UsageLimits(BaseModel):
    """Usage limits for AI models.
    
    Attributes:
        max_requests_per_minute: Maximum requests per minute
        max_input_tokens: Maximum input tokens per request
        max_output_tokens: Maximum output tokens per request
        max_parallel_requests: Maximum parallel requests
    """
    max_requests_per_minute: int
    max_input_tokens: int
    max_output_tokens: int
    max_parallel_requests: int = 5

class AIResponse(BaseModel):
    """Response from AI operation.

    Attributes:
        content: The generated content from the AI model
        usage: Information about token usage
        model: The model that generated the response
        finish_reason: The reason why generation stopped
    """
    content: str
    usage: Dict[str, int]
    model: str
    finish_reason: Optional[str] = None

    model_config = {
        'validate_assignment': True,
        'extra': 'forbid'
    }
```

### `/src/ailf/ai/engine.py`

```python
"""Enhanced AI engine for model interactions.

This module provides a unified interface for interacting with various
AI model providers including OpenAI, Google Gemini and Anthropic.
"""
from typing import Any, Dict, List, Optional, Union
import asyncio
import os
import logging
from pydantic import BaseModel, Field

from ..schemas.ai import AIResponse, ModelConfig, ModelProvider

class AIEngine:
    """Main AI engine for interacting with language models.
    
    This class provides a unified interface for working with different AI providers
    and handles common operations like rate limiting, fallbacks, and error handling.
    
    Attributes:
        provider: The model provider to use
        model: The specific model to use
        api_key: API key for the provider
    """
    
    def __init__(self, 
                 provider: ModelProvider = ModelProvider.OPENAI,
                 model: Optional[str] = None,
                 api_key: Optional[str] = None):
        """Initialize the AI engine.
        
        Args:
            provider: The AI provider to use
            model: The model to use (defaults to provider's default model)
            api_key: API key (defaults to environment variable based on provider)
        """
        self.logger = logging.getLogger(self.__class__.__name__)
        self.provider = provider
        self.api_key = api_key or self._get_api_key_for_provider(provider)
        self.model = model or self._get_default_model(provider)
        self.adapter = self._get_adapter(provider)
        
    def _get_api_key_for_provider(self, provider: ModelProvider) -> str:
        """Get API key from environment variables based on provider.
        
        Args:
            provider: The AI provider
            
        Returns:
            The API key from environment variables
            
        Raises:
            ValueError: If API key is not found in environment variables
        """
        env_var_map = {
            ModelProvider.OPENAI: "OPENAI_API_KEY",
            ModelProvider.ANTHROPIC: "ANTHROPIC_API_KEY",
            ModelProvider.GEMINI: "GOOGLE_API_KEY",
        }
        env_var = env_var_map.get(provider)
        if not env_var:
            raise ValueError(f"Unsupported provider: {provider}")
            
        api_key = os.environ.get(env_var)
        if not api_key:
            raise ValueError(f"API key not found in environment variable {env_var}")
            
        return api_key
        
    async def generate(self, prompt: str) -> AIResponse:
        """Generate a response from the AI model.
        
        Args:
            prompt: The prompt to send to the model
            
        Returns:
            AIResponse: The response from the model
            
        Raises:
            NotImplementedError: If the provider does not implement this method
        """
        raise NotImplementedError("Provider must implement generate method")
class AIEngine:
    """Unified AI engine for interacting with various provider models."""
    
    def __init__(
        self, 
        provider: Union[str, ModelProvider] = ModelProvider.OPENAI,
        model: Optional[str] = None,
        api_key: Optional[str] = None,
        fallback_providers: Optional[List[str]] = None
    ):
        """Initialize the AI engine.
        
        Args:
            provider: The AI provider to use (openai, gemini, anthropic)
            model: The specific model to use (defaults to provider's default)
            api_key: API key (if None, will load from environment)
            fallback_providers: List of providers to try if primary fails
        """
        self.provider = provider if isinstance(provider, ModelProvider) else ModelProvider(provider)
        self.model = model or self._get_default_model()
        self.api_key = api_key or self._get_api_key()
        self.adapter = self._create_adapter()
        self.fallback_providers = fallback_providers or []
        
    async def generate(self, prompt: str) -> AIResponse:
        """Generate a response from the AI model.
        
        Args:
            prompt: The prompt to send to the model
            
        Returns:
            AIResponse: The generated response
            
        Raises:
            AIEngineError: If the generation fails
        """
        try:
            return await self.adapter.generate(prompt)
        except Exception as e:
            if self.fallback_providers:
                # Try fallback providers
                return await self._try_fallbacks(prompt)
            raise AIEngineError(f"Generation failed: {str(e)}") from e
```

### `/src/ailf/ai/__init__.py`

```python
"""AI module for working with large language models.

This module provides a unified interface for interacting with different 
AI providers like OpenAI, Google's Gemini, and Anthropic's Claude.

Example:
    >>> from ailf.ai import AIEngine
    >>> engine = AIEngine(provider="openai", model="gpt-4o")
    >>> response = await engine.generate("Write a short story about AI")
    >>> print(response.content)
"""

from .engine import AIEngine, AIEngineError, ProviderAdapter
from .providers import OpenAIAdapter, GeminiAdapter, AnthropicAdapter

__all__ = [
    "AIEngine", 
    "AIEngineError",
    "ProviderAdapter",
    "OpenAIAdapter",
    "GeminiAdapter",
    "AnthropicAdapter"
]
```

### `/src/ailf/ai/providers/openai.py`

```python
"""OpenAI-specific adapter implementation.

This module provides the OpenAI implementation of the provider adapter.
"""
import os
from typing import Dict, Optional, List
import logging

from openai import AsyncOpenAI
from openai.types.chat import ChatCompletion

from ...schemas.ai import AIResponse
from ..engine import ProviderAdapter, AIEngineError

logger = logging.getLogger(__name__)

class OpenAIAdapter(ProviderAdapter):
    """OpenAI adapter for the AI engine."""
    
    def __init__(self, api_key: Optional[str] = None, model: str = "gpt-4o"):
        """Initialize the OpenAI adapter.
        
        Args:
            api_key: OpenAI API key (defaults to OPENAI_API_KEY env var)
            model: Model name to use (defaults to gpt-4o)
        """
        api_key = api_key or os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise AIEngineError("OpenAI API key not provided")
        
        super().__init__(api_key, model)
        self.client = AsyncOpenAI(api_key=self.api_key)
        
    async def generate(self, prompt: str) -> AIResponse:
        """Generate a response using OpenAI models.
        
        Args:
            prompt: The prompt to send to the model
            
        Returns:
            AIResponse: The generated response
            
        Raises:
            AIEngineError: If the request fails
        """
        try:
            response: ChatCompletion = await self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": prompt}]
            )
            
            content = response.choices[0].message.content or ""
            usage = {
                "prompt_tokens": response.usage.prompt_tokens,
                "completion_tokens": response.usage.completion_tokens,
                "total_tokens": response.usage.total_tokens
            }
            
            return AIResponse(
                content=content,
                usage=usage,
                model=self.model,
                finish_reason=response.choices[0].finish_reason
            )
        except Exception as e:
            logger.error(f"OpenAI request failed: {str(e)}")
            raise AIEngineError(f"OpenAI request failed: {str(e)}")
```

## Component Relationships

The AI module components work together to provide a unified interface for AI model interactions:

1. The `AIEngine` class serves as the main entry point, allowing users to interact with AI models
2. Provider-specific adapters handle the actual API calls to different AI services
3. Schemas define the data structures for requests and responses
4. Error handling provides a consistent way to handle failures
5. Fallback mechanisms allow graceful degradation when primary providers fail

This modular design makes it easy to add new providers or capabilities while maintaining a consistent API for developers.

# Initialize logging and monitoring
logger = setup_logging('ai_engine')
monitoring = setup_monitoring('ai_engine')

# Type variable for output types
T = TypeVar('T')

# AIEngine class would be implemented here with the same functionality
# but with updated imports and organization

# Exception classes
class AIEngineError(Exception):
    """Base exception for AI engine errors."""
    pass

class ModelError(AIEngineError):
    """Exception for model-specific errors."""
    pass

class ContentFilterError(AIEngineError):
    """Exception for content that was filtered by safety settings."""
    pass

# AIEngine class would continue here...
```

This example demonstrates how the reorganized code structure provides better organization, clearer separation of concerns, and improved modularity.

## Benefits of Reorganization

1. **Improved Modularity**: Each component has a clear responsibility.
2. **Better File Organization**: Related files are grouped together.
3. **Clearer Imports**: Import paths clearly indicate which component is being used.
4. **Easier Maintenance**: Smaller, more focused files are easier to maintain.
5. **Better Extensibility**: New provider implementations can be added without modifying the core engine.
6. **Enhanced Documentation**: Documentation is organized by component.
7. **Clearer Dependencies**: Dependencies between components are more explicit.

These principles can be applied across the entire repository to improve code organization and maintainability.

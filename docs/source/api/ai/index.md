# AI Components

This section documents the AI components of the AILF library.

```{toctree}
:maxdepth: 2

engine
engine_factory
anthropic_engine
openai_engine
```

The AI module provides standardized interfaces for working with various LLM providers and models.

## Key Components

- **AI Engine**: Base interface for LLM interactions
- **Provider-specific Engines**: Implementations for different AI providers
- **Engine Factory**: Factory pattern for creating the right engine instance
- **Caching**: Mechanisms for caching LLM responses

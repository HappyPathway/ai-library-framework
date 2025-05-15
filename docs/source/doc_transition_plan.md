# Documentation Transition Plan

This document explains the current documentation state during the transition from a flat project structure to a src-based layout.

## Current Status

The AILF library is currently in transition from a flat structure to a more organized src-based layout used by many professional Python packages:

1. **Legacy Structure**: Original code in `/ailf/`, `/utils/`, and `/schemas/` directories
2. **New Structure**: New code in `/src/ailf/` with proper subpackages

The documentation generation system has been updated to support both structures, but you may encounter warnings or missing documentation during this transition period.

## How to Write Documentation

### For New Code

All new code should be added to the src-based structure and documented there:

1. Place your code in the appropriate directory under `/src/ailf/`
2. Use Google-style docstrings for all classes, functions, and modules
3. Include examples in your docstrings where appropriate
4. Reference other modules using their src-based import paths

Example of a properly documented module in the new structure:

```python
"""AI provider adapter for OpenAI models.

This module implements the adapter pattern for OpenAI's API, providing a 
consistent interface to the AIEngine.
"""

from typing import Dict, Optional, List
import os
import logging

from ...schemas.ai import AIResponse, ModelConfig

class OpenAIAdapter:
    """Adapter for OpenAI models.
    
    Args:
        api_key: OpenAI API key (defaults to OPENAI_API_KEY env var)
        model: Model name to use (defaults to gpt-4o)
    """
    
    def __init__(self, api_key: Optional[str] = None, model: str = "gpt-4o"):
        """Initialize the adapter with API key and model."""
        # Implementation...
        
    async def generate(self, prompt: str, **kwargs) -> AIResponse:
        """Generate a response from the OpenAI model.
        
        Args:
            prompt: The prompt to send to the model
            **kwargs: Additional keyword arguments for the OpenAI API
            
        Returns:
            AIResponse: The generated response
            
        Raises:
            AIEngineError: If the request fails
            
        Example:
            ```python
            adapter = OpenAIAdapter()
            response = await adapter.generate("Tell me about AI")
            print(response.content)
            ```
        """
        # Implementation...
```

### For Existing Code

If you need to update documentation for legacy code:

1. First, check if the module has been migrated to the src-based structure
2. If it has, update the documentation in the new location
3. If not, update the documentation in the old location, but note that it will eventually be migrated

## Documentation Generation

The documentation system now supports both old and new structures:

1. API documentation is generated automatically from docstrings
2. User guides and examples are written as Markdown files

To build the documentation:

```bash
cd /workspaces/template-python-dev/docs
./build_docs.sh
```

## Known Issues

During the transition period, you may encounter:

1. Import errors for modules that haven't been migrated yet
2. Duplicate documentation for modules that exist in both structures
3. Broken cross-references between old and new structure

These issues will be resolved as the migration progresses.

## Legacy Documentation

Older documentation files that were part of the original project structure have been moved to a separate directory:

```
docs/legacy/
```

These files are kept for historical reference but are not included in the generated documentation. They may contain outdated information or references to the previous repository structure.

If you need to reference these older documents, you can find them directly in the repository but be aware they may not reflect the current state of the project.

## Migration Timeline

1. **Phase 1** (Current): Dual structure with documentation support for both
2. **Phase 2**: Complete migration of all modules to src-based structure
3. **Phase 3**: Remove legacy structure and simplify documentation generation

## Best Practices for Documentation

1. Write clear and concise docstrings
2. Include type annotations for all function parameters and return values
3. Provide examples for non-trivial functions and classes
4. Keep module-level docstrings informative about the module's purpose
5. Use cross-references to link related components
6. Follow the Google Python Style Guide for docstrings

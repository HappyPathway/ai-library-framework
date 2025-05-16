# Import Patterns for AILF Project

This guide explains the recommended import patterns to use when working with the AILF library, considering both the new src-based structure and legacy modules.

## Src-Based Import Patterns

### For External Users

When using the AILF package as an installed dependency, imports should be done from the main package:

```python
# Core components
from ailf import AIEngine, setup_logging, TaskManager

# Specific modules
from ailf.ai import OpenAIAdapter, GeminiAdapter
from ailf.core.logging import configure_logger
from ailf.schemas.ai import AIResponse
from ailf.messaging.zmq import ZMQPublisher, ZMQSubscriber
```

### For Internal Development

When developing code within the package itself:

#### Absolute Imports (Preferred)

```python
# From one module to another
from ailf.core.logging import setup_logging
from ailf.schemas.ai import AIResponse
```

#### Relative Imports (When appropriate)

```python
# When in src/ailf/ai/providers/openai.py importing from src/ailf/schemas/ai.py
from ....schemas.ai import AIResponse

# When in src/ailf/ai/__init__.py importing from src/ailf/ai/providers/openai.py
from .providers.openai import OpenAIAdapter
```

## Legacy Import Patterns

Until the migration is complete, some code still exists in the legacy structure. For these modules:

### Importing Legacy Code from Legacy Code

```python
# From utils/ to other utils/ modules
from utils.core.logging import setup_logging

# From utils/ to schemas/
from schemas.ai import AIResponse

# From schemas/ to utils/
from utils.ai_engine import AIEngine
```

### Importing Legacy Code from Src-Based Code

For the transition period, you might need to import from legacy modules in new code:

```python
# Not recommended but sometimes necessary during transition
import sys
import os

# Add the project root to path if needed
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../.."))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

# Import from legacy modules
from utils.ai_engine import AIEngine
from schemas.ai import AISchema
```

## Import Best Practices

1. **Prefer Explicit Imports**: Avoid wildcard imports like `from module import *`
2. **Group Imports**: Follow the standard order - standard library, third-party, local
3. **Import the Right Level**: Import what you need, not the parent package
4. **Circular Imports**: Avoid them by restructuring or using import inside function
5. **Type Hints**: Use string literals for forward references to avoid circular imports
6. **Module Location Independence**: Avoid hardcoded paths or `__file__` manipulation

### Example of Proper Import Grouping

```python
# Standard library
import os
import sys
from typing import Dict, List, Optional

# Third-party packages
import numpy as np
from pydantic import BaseModel

# AILF package - core
from ailf.core.logging import setup_logging
from ailf.core.monitoring import MetricsCollector

# AILF package - current module relatives
from .providers import OpenAIAdapter
from .schemas import ModelResponse
```

## Handling Transitional Imports

During the transition period, some modules may exist in both the legacy and src-based structure. The import system has been set up to prioritize the src-based structure, but conflicts can arise.

To handle this:

1. Always check which version of the module you're importing
2. Use explicit import paths where possible
3. Consider adding comments to clarify import sources
4. Be aware that some modules may temporarily have duplicate implementations

Once the migration is complete, all imports should follow the src-based pattern.

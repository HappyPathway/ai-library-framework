# Handling Unused Imports in Python

This guide provides multiple ways to suppress or manage unused import warnings in your Python code.

## Option 1: Using inline comments

For individual unused imports:

```python
from module import UnusedClass  # noqa: F401
```

For a whole file:

```python
# flake8: noqa
import os
import sys
import json  # All these can be unused without warnings
```

## Option 2: Using configuration files

This repository is already set up with multiple configuration files:

- `.flake8` - Controls Flake8 behavior
- `.pylintrc` - Controls Pylint behavior
- `pyproject.toml` - Modern Python tooling configuration
- `setup.cfg` - Alternative configuration

## Option 3: Import as needed

When you know certain imports will be used later or in certain situations, consider using:

```python
if some_condition:
    import module_only_needed_sometimes
```

## Option 4: Use __all__ to control exports

In module files, define what's exported to control imports in `__init__.py` files:

```python
__all__ = ['ActuallyUsedClass', 'ActuallyUsedFunction']

from .submodule import (
    ActuallyUsedClass,  # Used externally
    ActuallyUsedFunction,  # Used externally
    _PrivateClass,  # Only used internally
)
```

## VS Code Configuration

The VS Code settings have been updated to ignore unused import warnings with Pylance/Pyright.

## For MCP-specific Imports

If you're dealing with Model Context Protocol imports, you might need specific imports for type checking.
Use type checking guards:

```python
import typing
if typing.TYPE_CHECKING:
    from some_module import SomeType  # Will only be imported during type checking
```

# Understanding the src-based Layout

This guide explains the transition from a flat project structure to a standardized src-based layout and how to work with the new structure.

## What is a src-based Layout?

A src-based layout is a Python project structure where the actual package code lives in a `src` directory rather than at the project root. The structure looks like this:

```
project_root/
├── src/
│   └── package_name/
│       ├── __init__.py
│       ├── module1.py
│       └── moduleN.py
├── tests/
├── docs/
├── setup.py  # or pyproject.toml
└── README.md
```

## Benefits of src-based Layout

1. **Clean separation**: Separates package code from project supporting files
2. **Prevents accidental imports**: Makes it harder to accidentally import from the project directory instead of from an installed package
3. **Testing against installed version**: Ensures your tests run against the installed version of your package
4. **Better compatibility**: Works better with modern packaging tools like setuptools, build, hatch, etc.
5. **Standardization**: Follows a common pattern used by many Python projects

## How the AILF Project is Organized

The AILF library is organized in a src-based layout:

```
template-python-dev/
├── src/
│   └── ailf/
│       ├── __init__.py
│       ├── agent/          # Core agent functionality
│       ├── ai/             # AI-specific functionality
│       ├── cloud/          # Cloud service integrations 
│       ├── core/           # Core utilities
│       ├── messaging/      # Messaging infrastructure
│       ├── schemas/        # Data models
│       └── storage/        # Storage implementations
├── tests/                  # Test suite
├── docs/                   # Documentation
├── examples/               # Example implementations
└── pyproject.toml          # Project metadata and configuration
```

## Legacy Structure

The project is in transition from a flat structure. Legacy code may still exist in:

- `/ailf/`: Legacy main package (being migrated to `/src/ailf/`)
- `/utils/`: Legacy utilities (being migrated to `/src/ailf/`)
- `/schemas/`: Legacy schema definitions (being migrated to `/src/ailf/schemas/`) 

## Import Patterns

When working with the src-based layout, imports should follow these patterns:

### From External Code (Outside the Project)

```python
from ailf.core.logging import setup_logging
from ailf.agent import Agent
from ailf.schemas.ai import AIConfig
```

### From Inside the Package

When writing code inside the `src/ailf` package, you can use relative imports:

```python
from .core.logging import setup_logging  # When in src/ailf/__init__.py
from ..core.logging import setup_logging  # When in src/ailf/agent/__init__.py
```

Or absolute imports:

```python
from ailf.core.logging import setup_logging
```

## Development Installation

To work on the project, you should install it in development mode:

```bash
pip install -e .
```

This will create a link to the package in your Python environment, allowing you to modify the code and see the changes without reinstalling.

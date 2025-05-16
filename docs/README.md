# Documentation Generation

This directory contains the documentation for the AILF project, built using Sphinx and MyST Markdown.

## Directory Structure

```
docs/
├── build/                  # Generated documentation output
│   ├── html/               # HTML output
│   └── markdown/           # Markdown output (if generated)
├── source/                 # Documentation source files
│   ├── api/                # Auto-generated API reference documentation
│   ├── guides/             # User guides and tutorials
│   ├── examples/           # Example code documentation
│   ├── _static/            # Static assets
│   ├── _templates/         # Sphinx templates
│   ├── conf.py             # Sphinx configuration
│   ├── index.md            # Main documentation landing page
│   └── api_structure_updated.py # Script to generate API docs structure
├── legacy/                 # Older documentation files (not included in builds)
├── Makefile                # Sphinx build makefile
└── build_docs.sh           # Script to automate documentation generation
```

## Building the Documentation

### Using the Build Script

The simplest way to build the documentation is to use the provided build script:

```bash
./build_docs.sh
```

This script:
1. Creates a virtual environment if it doesn't exist
2. Installs required dependencies
3. Generates the API documentation structure
4. Builds the HTML documentation

### Manual Build Process

If you prefer to build the documentation manually:

1. Make sure you have the required dependencies installed:
```bash
pip install sphinx sphinx-markdown-builder myst-parser
```

2. Generate the API structure:
```bash
python docs/source/api_structure_updated.py
```

3. Build the documentation:
```bash
cd docs
make html
```

## Documentation Structure

### Source Structure

- `index.md`: Main landing page and table of contents
- `api/`: Auto-generated API reference documentation
- `guides/`: User guides and tutorials
- `examples/`: Code examples with explanations

### API Reference Generation

The API reference documentation is automatically generated from the Python source code. The script `api_structure_updated.py` scans both:

1. The src-based package structure (`src/ailf/`)
2. Legacy module directories (`utils/`, `agent/`, `schemas/`)

To add a new module to the documentation, ensure:
1. The module has proper docstrings (Google style docstrings are recommended)
2. The module is properly importable from the project root

## Writing Documentation

### Docstring Format

We use Google-style docstrings for Python code. Example:

```python
def my_function(param1: str, param2: int = 42) -> bool:
    """Short description of the function.
    
    More detailed explanation of the function's behavior.
    
    Args:
        param1: Description of param1
        param2: Description of param2, defaults to 42
        
    Returns:
        Description of return value
        
    Raises:
        ValueError: If param1 is empty
        
    Example:
        >>> result = my_function("test", 10)
        >>> print(result)
        True
    """
```

### Markdown Files

Markdown files should use standard Markdown syntax with MyST extensions for advanced features.

## Viewing Documentation

After building, the HTML documentation can be found in `docs/build/html/`. Open `index.html` in a web browser to view it.

# Contributing Documentation

This guide explains how to contribute to the AILF project's documentation.

## Documentation Structure

The documentation for this project consists of:

1. **API Reference**: Auto-generated from docstrings in the code
2. **User Guides**: Hand-written explanations for specific topics
3. **Examples**: Documented code samples demonstrating usage
4. **Project Reference**: Overall architecture and design documentation

## Writing Docstrings

When writing code, follow these guidelines for docstrings:

### Module Docstrings

Every Python module should have a docstring at the top of the file:

```python
"""Brief description of the module.

More detailed description explaining the module's purpose,
key concepts, and how it fits into the overall system.

Examples:
    Example usage if applicable

Notes:
    Any important notes or caveats
"""
```

### Class Docstrings

For classes, follow the Google-style format:

```python
class MyClass:
    """Short description of the class.
    
    Longer description explaining the class's purpose,
    behavior, and how it should be used.
    
    Attributes:
        attr_name: Description of the attribute
        another_attr: Description of another attribute
        
    Args:
        param1: Description of the first constructor parameter
        param2: Description of the second constructor parameter
    """
```

### Method and Function Docstrings

For methods and functions:

```python
def my_function(param1, param2):
    """Short description of what the function does.
    
    More detailed explanation if needed.
    
    Args:
        param1 (type): Description of param1
        param2 (type): Description of param2
        
    Returns:
        return_type: Description of the return value
        
    Raises:
        ExceptionType: When and why this exception is raised
        
    Examples:
        ```python
        result = my_function("value", 42)
        ```
    """
```

## Creating User Guides

User guides are written in Markdown and stored in the `docs/source/guides/` directory:

1. Create a new `.md` file in the guides directory
2. Add front matter with title and description
3. Write content using Markdown and MyST extensions
4. Add code examples where appropriate
5. Include the guide in the appropriate toctree in `index.md`

### Example Guide Structure

```markdown
<!-- filepath: /workspaces/template-python-dev/docs/source/guides/my_guide.md -->
# My Guide Title

This guide explains how to use Feature X in the AILF framework.

## Overview

Brief explanation of the feature and its purpose.

## Installation

```bash
pip install "ailf[feature-x]"
```

## Basic Usage

```python
from ailf.feature_x import SomeClass

obj = SomeClass()
result = obj.do_something()
```

## Advanced Topics

More detailed content...

## Troubleshooting

Common issues and solutions...
```

## Adding to the Documentation

1. **Add New API Documentation**: Simply add proper docstrings to your code
2. **Add New User Guide**:
   - Create a new Markdown file in `docs/source/guides/`
   - Add it to the appropriate toctree in `index.md`
3. **Add New Example**:
   - Add a well-documented example script to the `examples/` directory
   - Create a corresponding Markdown file in `docs/source/examples/`
   - Add it to the examples toctree in `index.md`

## Building and Testing Documentation

Before submitting your changes, always build and test the documentation:

```bash
cd /workspaces/template-python-dev/docs
./build_docs.sh
```

Then open `docs/build/html/index.html` in a browser to review your changes.

## Documentation Style Guide

1. **Use present tense**: "This function returns..." not "This function will return..."
2. **Be concise**: Get to the point without unnecessary words
3. **Use active voice**: "The function processes data" not "Data is processed by the function"
4. **Be specific**: Avoid vague terms like "various" or "several"
5. **Include examples**: Especially for complex functionality
6. **Use proper formatting**:
   - *Italics* for emphasis
   - **Bold** for strong emphasis
   - `Monospace` for code, file names, and technical terms
   - Bulleted lists for unordered items
   - Numbered lists for sequential steps

## A Note About Cross-References

During the transition to the src-based layout, some cross-references may break. When creating cross-references:

1. Use relative paths where possible: `../topic/file.md`
2. For API references, use the full import path: `ailf.module.Class`
3. If referencing content that might move, consider using a more general reference

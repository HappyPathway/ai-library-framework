# Installation Guide

## Requirements

AILF-Kagent requires:

- Python 3.8+
- AILF library
- Kagent library

## Standard Installation

You can install AILF-Kagent directly from PyPI:

```bash
pip install ailf-kagent
```

## Development Installation

For development, it's recommended to install the package in editable mode with development dependencies:

```bash
# Clone the repository
git clone https://github.com/your-org/ailf-kagent.git
cd ailf-kagent

# Install in development mode
pip install -e ".[dev]"
```

## Using Makefile

The project includes a Makefile with common commands:

```bash
# Install for development
make dev-install

# Run tests
make test

# Format code
make format

# Run linting
make lint
```

## Verifying Installation

To verify that AILF-Kagent is installed correctly:

```python
import ailf_kagent
print(ailf_kagent.__version__)
```

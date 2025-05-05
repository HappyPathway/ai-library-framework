# Development Setup Guide

This guide explains how to set up your development environment for the Python Agent Development Template project.

## Installation

### Installing in Development Mode

When installing this package in development mode, always run the following command from the **root directory** of the project:

```bash
pip install -e .
```

### Using Feature Extras

The project supports various "extras" for installing specific feature dependencies:

```bash
# With specific features
pip install -e ".[ai]"      # AI-related dependencies
pip install -e ".[mcp]"     # Model Context Protocol dependencies
pip install -e ".[cloud]"   # Cloud service dependencies
pip install -e ".[zmq]"     # ZeroMQ messaging dependencies

# Combined features
pip install -e ".[ai,mcp]"  # For building an AI agent with MCP

# Development
pip install -e ".[dev]"     # Development and testing tools

# Full installation
pip install -e ".[all]"     # All available dependencies
```

## Common Issues

### Problematic `src` Directory Structure

Previously, the project installation could sometimes create a problematic `src/template-python-dev` directory containing a duplicate of the project. This structure could cause:

1. Import confusion with conflicting module paths
2. Linting errors due to duplicate code detection
3. Git issues when the directory contained its own `.git` folder

This issue has been fixed, but if you encounter it:

1. Uninstall the package: `pip uninstall template-python-dev`
2. Remove the `src` directory: `rm -rf src`
3. Install the package from the root directory: `pip install -e .`

## Using the Makefile

The project includes a Makefile with useful commands for development:

```bash
# Install dependencies and the package
make install

# Run tests
make test          # All tests
make test-unit     # Unit tests only
make test-integration # Integration tests only

# Generate test coverage report
make coverage

# Run linting
make lint

# Format code
make format
```

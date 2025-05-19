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

### Understanding the `src`-based Directory Structure

The project now follows a standard Python `src`-based layout structure. This means the main package code lives in:

```
src/ailf/
```

This structure provides several benefits:
1. Cleaner separation between package code and supporting files
2. Prevents accidental imports from the development environment
3. Better compatibility with automated build tools and packaging

When installing the package in development mode, the command:
```bash
pip install -e .
```

Will automatically create the right linking to the package in the `src` directory.

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

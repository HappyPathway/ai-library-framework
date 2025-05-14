# AI Liberation Front (AILF)

AI Liberation Front: Freedom tools for AI agent development

## About

This package provides a collection of utilities, patterns, and infrastructure components specifically designed to accelerate the development of AI agents with:

- Structured LLM interactions via Pydantic models
- Tool registration and management
- Distributed computing via ZeroMQ
- Configurable storage backends
- Comprehensive logging and monitoring
- Secure secret management
- Testing patterns for AI components

## Installation

```bash
# Basic installation
pip install ailf

# With AI support
pip install ailf[ai]

# With all features
pip install ailf[all]
```

## Documentation

For full documentation, visit [ailf.readthedocs.io](https://ailf.readthedocs.io/)

## Development

### Using the Dev Container

This project includes a development container configuration to ensure consistent development environments across different machines. The dev container includes all necessary dependencies and tools for AI agent development.

#### VS Code Dev Container

If you're using VS Code with the Remote - Containers extension:

1. Open the project in VS Code
2. When prompted, click "Reopen in Container"
3. Alternatively, press F1 and select "Remote-Containers: Reopen in Container"

#### GitHub Codespaces

You can also develop using GitHub Codespaces, which will automatically use the dev container configuration.

### CI/CD Workflows

Our GitHub Actions workflows use the same dev container configuration as local development, ensuring consistency across development and CI environments:

- **Build Dev Container**: Builds and publishes the dev container image when the container configuration changes
- **Integration Tests**: Runs tests in the dev container
- **Dev Container CI**: Tests the dev container build and functionality
- **Dev Container Tests**: Additional container-specific tests
- **Publish to PyPI**: Builds and publishes packages using the dev container

The workflows use the `devcontainers/ci` action to leverage the same development environment defined in the `.devcontainer` directory. This ensures that:

1. Local development (VS Code Dev Container)
2. CI/CD pipelines (GitHub Actions)
3. Production builds

All use identical environments, eliminating "works on my machine" issues.

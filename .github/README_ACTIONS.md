# GitHub Actions with Dev Container Integration

This project uses GitHub Actions workflows integrated with the same development container configuration used in VS Code. This ensures consistency between local development and CI/CD environments.

## Workflow Files

- **integration_tests.yml**: Runs tests for every push or pull request using the dev container
- **publish_to_pypi.yml**: Builds and publishes the package to PyPI on new releases
- **devcontainer_ci.yml**: Advanced workflow demonstrating additional capabilities

## How It Works

The workflows leverage GitHub's [devcontainers/ci](https://github.com/devcontainers/ci) action, which builds the container defined in `.devcontainer/devcontainer.json` and executes commands within it.

### Benefits

1. **Environment Parity**: CI/CD runs in the same environment as local development
2. **Reduced Configuration Drift**: Changes to dev container automatically apply to CI/CD
3. **Simplified Workflow Maintenance**: Dev environment and CI settings managed in one place

### Example Usage

To use the dev container locally:

1. Open the project in VS Code
2. When prompted, click "Reopen in Container"
3. VS Code will build and start the development container

To modify the container configuration:

1. Edit `.devcontainer/devcontainer.json` or `.devcontainer/Dockerfile`
2. Rebuild the container in VS Code
3. CI/CD workflows will use the updated container on next run

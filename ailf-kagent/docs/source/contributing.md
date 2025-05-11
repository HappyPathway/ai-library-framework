# Contributing to AILF-Kagent

We welcome contributions to the AILF-Kagent integration project! This document provides guidelines for contributing code, documentation, and bug reports.

## Development Environment

1. Fork the repository on GitHub
2. Clone your fork locally
3. Set up a development environment:
   ```bash
   cd ailf-kagent
   make dev-install
   ```

## Development Workflow

1. Create a feature branch from `main`:
   ```bash
   git checkout -b feature/your-feature-name
   ```

2. Make your changes, following our coding standards

3. Add tests for your changes

4. Run the test suite:
   ```bash
   make test
   ```

5. Format and lint your code:
   ```bash
   make format
   make lint
   ```

6. Commit your changes with descriptive commit messages

7. Push to your fork and submit a pull request

## Coding Standards

- Use type hints throughout the codebase
- Write docstrings for all public functions, classes, and methods
- Follow PEP 8 style guidelines
- Keep code modular and focused

## Testing

- Write unit tests for new functionality
- Ensure all tests pass before submitting
- Aim for high test coverage

## Documentation

- Update or add documentation for any changes
- Include examples for new features
- Keep API documentation up to date

## Issue Reporting

- Use the GitHub issue tracker
- Include steps to reproduce bugs
- Include Python and dependency versions
- Include relevant error messages and logs

## Pull Request Process

1. Update documentation as needed
2. Add or update tests
3. Ensure CI passes on your branch
4. Request review from maintainers
5. Address any feedback

## Code of Conduct

Please be respectful and professional when interacting with other contributors. We strive to maintain a welcoming and inclusive community.

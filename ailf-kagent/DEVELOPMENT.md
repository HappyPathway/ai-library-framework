# Development Notes

## Testing Environment

The tests for this package require both AILF and Kagent to be installed. Since we're developing an integration between these two frameworks, the tests use mocks to simulate the behavior of the external dependencies.

### Setting Up a Development Environment

1. Create a virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

2. Install development dependencies:
   ```bash
   pip install -e ".[dev]"
   ```

3. Install mock packages (if AILF and Kagent aren't available):
   ```bash
   pip install pytest-mock
   ```

### Running Tests with Mocks

To run the tests without having the actual dependencies installed, you can use the pytest-mock plugin. This is especially useful for CI/CD environments.

```bash
# From the project root
pytest tests/ --mock-modules=ailf,kagent
```

### Directories and Files

- `adapters/`: Core adapter implementations
  - `tools.py`: Tool adapters
  - `agents.py`: Agent adapters
  - `memory.py`: Memory adapters
  - `schemas.py`: Schema translation utilities

- `examples/`: Example implementations
  - `basic_integration.py`: Simple integration example
  - `advanced_usage.py`: Advanced integration features
  - `mcp_integration.py`: MCP server integration
  - `team_research.py`: Team-based workflow

- `tests/`: Test cases
  - `test_tool_adapters.py`: Tests for tool adapters
  - `test_agent_adapters.py`: Tests for agent adapters
  - `test_memory_bridge.py`: Tests for memory adapters
  - `test_schema_translation.py`: Tests for schema translation

## Common Development Tasks

- **Run Tests**: `make test`
- **Format Code**: `make format`
- **Lint Code**: `make lint`
- **Build Documentation**: `make docs`
- **Build Package**: `make build`

## Versioning

This package follows semantic versioning. The current version is defined in `__init__.py`.

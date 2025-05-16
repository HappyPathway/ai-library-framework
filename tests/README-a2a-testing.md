# A2A Protocol Testing in AILF Framework

This document explains the testing structure and how to run tests for the Agent-to-Agent (A2A) Protocol implementation in the AILF framework.

## Test Structure

The tests are organized into the following directories:

- **Unit Tests**: `/tests/unit/communication/test_a2a_*.py`
  - Test individual components in isolation with mocks
  - Fast execution, focused on correctness of component logic

- **Integration Tests**: `/tests/integration/communication/test_a2a_*.py`
  - Test interactions between multiple A2A components
  - Test end-to-end flows between servers

- **Performance Tests**: `/tests/performance/test_a2a_benchmarks.py`
  - Measure throughput, latency, and resource usage
  - Identify performance bottlenecks

- **End-to-End Tests**: `/tests/e2e/`
  - Test real-world workflows and scenarios
  - Use actual agent implementations

## Running Tests

### Running All A2A Tests

Use the provided script to run all A2A-related tests:

```bash
./run_a2a_tests.sh
```

### Running Specific Test Categories

To run only unit tests:

```bash
pytest tests/unit/communication/test_a2a_*.py
```

To run only integration tests:

```bash
pytest tests/integration/communication/test_a2a_*.py
```

To run performance benchmarks:

```bash
pytest tests/performance/test_a2a_benchmarks.py
```

### Testing with External A2A Implementations

To test interoperability with external A2A implementations:

1. Set up the external A2A server
2. Set the environment variable `EXTERNAL_A2A_SERVER_URL` to point to the server
3. Run the interoperability tests:

```bash
EXTERNAL_A2A_SERVER_URL=http://localhost:8080/v1 pytest tests/integration/communication/test_a2a_interoperability.py
```

## Test Coverage Report

To generate a test coverage report for A2A components:

```bash
pytest --cov=ailf.communication.a2a_ tests/unit/communication/test_a2a_*.py tests/integration/communication/test_a2a_*.py
```

## Adding New Tests

When adding new A2A tests:

1. Follow the existing naming convention (`test_a2a_*.py`)
2. Add unit tests for new components
3. Add integration tests for component interactions
4. Update the validation tracker in `/tests/validation_tracker.md`

## Future Test Improvements

- Complete E2E tests for real-world A2A applications
- Add tests for external A2A implementations (LangGraph, CrewAI, AG2)
- Expand performance benchmarks for different message sizes and concurrency levels

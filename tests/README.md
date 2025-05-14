# AILF Framework Testing Guide

This guide provides an overview of the AILF Framework testing architecture, explains how to run tests, and offers guidance for maintaining and extending the test suite.

## Testing Philosophy

The AILF Framework uses a comprehensive testing approach with multiple layers:

1. **Unit Tests**: Test individual components in isolation with mocks
2. **Integration Tests**: Test interactions between components
3. **Performance Tests**: Measure throughput, latency, and resource usage
4. **End-to-End Tests**: Test complete workflows in realistic scenarios
5. **Documentation Tests**: Ensure code examples in documentation are correct

## Directory Structure

```
tests/
├── conftest.py           # Global test configuration
├── README.md            # This file
├── validation_tracker.md # Track test implementation progress
├── unit/                # Unit tests
│   ├── conftest.py      # Unit test configuration
│   ├── communication/   # Communication module tests
│   │   ├── test_a2a_client.py
│   │   ├── test_a2a_datetime_serialization.py
│   │   ├── test_a2a_orchestration.py
│   │   ├── test_a2a_push.py
│   │   ├── test_a2a_registry.py
│   │   └── test_a2a_server.py
│   ├── cognition/       # Cognition module tests
│   ├── feedback/        # Feedback module tests
│   └── ...              # Tests for other modules
├── integration/         # Integration tests
│   ├── conftest.py      # Integration test configuration
│   ├── communication/   # Communication integration tests
│   │   ├── test_a2a_interoperability.py
│   │   ├── test_a2a_orchestration_flow.py
│   │   ├── test_a2a_protocol_flow.py
│   │   └── test_a2a_push_notifications.py
│   └── ...              # Tests for other integrations
├── e2e/                 # End-to-end tests
│   ├── conftest.py      # E2E test configuration
│   └── test_a2a_e2e.py  # E2E tests for A2A protocol
├── performance/         # Performance benchmarks
│   └── test_a2a_benchmarks.py  # Performance tests for A2A components
└── docs/                # Documentation tests
    ├── __init__.py
    └── test_a2a_documentation.py  # Tests for documentation examples
```

## Running Tests

### Running All Tests

To run all validation tests with coverage reporting:

```bash
./run_validation_tests.sh
```

### Running A2A-Specific Tests

To run all A2A-related tests:

```bash
./run_a2a_tests.sh
```

### Running Specific Test Categories

To run specific test categories:

```bash
# Unit tests
pytest tests/unit

# Integration tests
pytest tests/integration

# A2A tests only
pytest tests/unit/communication/test_a2a_*.py tests/integration/communication/test_a2a_*.py

# Documentation tests
pytest tests/docs

# End-to-end tests
pytest tests/e2e

# Performance tests
pytest tests/performance
```

### Generating Coverage Reports

To generate a coverage report:

```bash
pytest --cov=ailf --cov-report=html:coverage_html --cov-report=term tests/
```

Then open `coverage_html/index.html` in a browser.

## Adding New Tests

When adding new tests, follow these guidelines:

1. **Use the Right Test Level**:
   - Unit tests for isolated component testing
   - Integration tests for testing component interactions
   - E2E tests for complete workflows
   - Performance tests for measuring efficiency

2. **Follow Naming Conventions**:
   - File names should start with `test_`
   - Test classes should start with `Test`
   - Test methods should start with `test_`

3. **Use Fixtures Properly**:
   - Common setup should be in fixtures
   - Use appropriate fixture scopes (`function`, `class`, `module`, `session`)

4. **Write Clear Test Names**:
   - Test names should describe what is being tested
   - Use the format `test_<function>_<scenario>_<expected result>`

5. **Update Validation Tracker**:
   - Mark completed tests in `validation_tracker.md`

## Special Test Types

### End-to-End Tests

End-to-end tests simulate real-world usage scenarios. These tests are resource-intensive and slower to run, so they're disabled by default.

To enable E2E tests:

```bash
RUN_E2E_TESTS=1 ./run_validation_tests.sh
```

Some E2E tests that start actual servers are marked with `@slow_tests` and can be enabled with:

```bash
RUN_SLOW_TESTS=1 pytest tests/e2e
```

### Performance Benchmarks

Performance tests measure the efficiency of critical components. Run them in isolation for more accurate results:

```bash
pytest tests/performance
```

For detailed benchmarks with multiple runs:

```bash
pytest tests/performance --benchmark-sort=mean --benchmark-columns=min,max,mean,stddev
```

### Documentation Tests

Documentation tests ensure code examples in the documentation are valid and up-to-date:

```bash
pytest tests/docs
```

## Test Markers

The test suite uses the following pytest markers:

- `@pytest.mark.asyncio` - Used for async tests
- `@pytest.mark.integration` - Integration tests
- `@pytest.mark.e2e` - End-to-end tests
- `@pytest.mark.performance` - Performance tests
- `@pytest.mark.docs` - Documentation tests
- `@pytest.mark.benchmark` - Benchmarking tests
- `@pytest.mark.interop` - Interoperability tests

## Mocking Strategy

1. **Unit Tests**: Mock all external dependencies
2. **Integration Tests**: Use real implementations of AILF components, but mock external services
3. **E2E Tests**: Use real implementations where possible, including starting test servers

## Continuous Integration

The test suite is designed to run in CI environments. The following jobs should be configured:

1. **Fast Tests**: Run unit and integration tests on every PR
2. **Full Tests**: Run all tests including E2E tests on merges to main branch
3. **Coverage Report**: Generate and publish coverage reports

## Tips for Effective Tests

1. **Isolate Tests**: Each test should be independent and not rely on state from other tests
2. **Clean Up Resources**: Tests should clean up after themselves, especially when creating external resources
3. **Use Meaningful Assertions**: Assert exactly what you're testing
4. **Test Edge Cases**: Include tests for error conditions and boundary cases
5. **Keep Tests Fast**: Optimize test setup and teardown for speed

## Contributing New Tests

When contributing new tests:

1. First check `validation_tracker.md` to see what tests are needed
2. Follow the existing structure and patterns
3. Ensure tests are properly documented
4. Add appropriate markers
5. Update the validation tracker when complete

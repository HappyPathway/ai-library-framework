# Testing Guide

## Running Tests

This project uses pytest for testing. There are both unit tests and integration tests.

### Unit Tests

To run unit tests:

```bash
pytest tests/utils
```

### Integration Tests

Integration tests may require external services like Redis. You can run them with:

```bash
pytest tests/integration
```

## Redis Testing Strategy

Redis is used for messaging and caching in this project, and several integration tests require a Redis server.

### Options for Redis Tests

1. **Use a local Redis server**:
   ```bash
   # Start Redis if it's not running
   sudo service redis-server start
   # Run Redis tests
   pytest tests/integration/utils/test_redis.py
   ```

2. **Use the mock Redis implementation**:
   ```bash
   # Set environment variable to use mock implementation
   export USE_MOCK_REDIS=true
   # Run Redis tests
   pytest tests/integration/utils/test_redis.py
   ```

3. **Use automatic fallback**:
   ```bash
   # Set environment variable to use mock if Redis is unavailable
   export USE_MOCK_REDIS_FALLBACK=true
   # Run the helper script that checks Redis and runs tests
   ./setup/check_redis.sh pytest tests/integration/utils/test_redis.py
   ```

### Redis in CI Environment

In CI workflows, we provide two methods for handling Redis tests:

1. **Service Container**: The main CI workflow uses a Redis service container
2. **Dev Container**: The devcontainer workflow tests with both Redis and mock implementations

## Mocking Strategy

The `utils/messaging/mock_redis.py` module provides mock implementations of Redis clients for testing
without a Redis server. These are automatically used when:

- The `USE_MOCK_REDIS` environment variable is set to `true`
- Redis is unavailable and `USE_MOCK_REDIS_FALLBACK` is set to `true`

This allows tests to run in environments without Redis while still providing good test coverage.

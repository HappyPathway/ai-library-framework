#!/bin/bash
# Check Redis availability and set environment accordingly

# Default Redis settings
REDIS_HOST=${REDIS_HOST:-localhost}
REDIS_PORT=${REDIS_PORT:-6379}

echo "Checking Redis availability at $REDIS_HOST:$REDIS_PORT..."

# Try to ping Redis
if redis-cli -h "$REDIS_HOST" -p "$REDIS_PORT" ping > /dev/null 2>&1; then
    echo "Redis server is available! Using actual Redis implementation."
    # Unset USE_MOCK_REDIS in case it was set before
    unset USE_MOCK_REDIS
else
    echo "Redis server is not available!"
    
    # Check if we should use mock implementation
    if [ "${USE_MOCK_REDIS_FALLBACK:-false}" = "true" ]; then
        echo "Configuring environment to use mock Redis implementation."
        export USE_MOCK_REDIS=true
    else
        echo "WARNING: Tests requiring Redis may fail."
        echo "Set USE_MOCK_REDIS=true to use mock implementation,"
        echo "or USE_MOCK_REDIS_FALLBACK=true to auto-fallback to mock."
    fi
fi

# Execute the command passed to this script
if [ $# -gt 0 ]; then
    echo "Executing: $@"
    exec "$@"
fi

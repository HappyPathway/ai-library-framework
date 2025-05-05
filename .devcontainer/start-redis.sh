#!/bin/bash
# Start Redis server if it's not already running

# Create Redis configuration for development if it doesn't exist
REDIS_CONF="/tmp/redis-dev.conf"
if [ ! -f "$REDIS_CONF" ]; then
    echo "Creating Redis development configuration..."
    cat > "$REDIS_CONF" <<EOL
# Redis development configuration
port 6379
daemonize yes
loglevel notice
logfile /tmp/redis-dev.log
databases 16
save 900 1
save 300 10
save 60 10000
rdbcompression yes
dbfilename dump.rdb
dir /tmp
appendonly no
maxmemory 128mb
maxmemory-policy volatile-lru
EOL
    echo "✓ Redis configuration created"
fi

# Check if Redis is running
if ! pgrep -x "redis-server" > /dev/null; then
    echo "Starting Redis server with development configuration..."
    redis-server "$REDIS_CONF"
    sleep 1
    
    # Verify Redis is running
    if pgrep -x "redis-server" > /dev/null; then
        echo "✓ Redis server started successfully"
    else
        echo "× Failed to start Redis server"
        exit 1
    fi
else
    echo "✓ Redis server is already running"
fi

# Test Redis connection
if redis-cli ping | grep -q "PONG"; then
    echo "✓ Redis connection successful"
else
    echo "× Redis connection failed"
    exit 1
fi

echo "Redis is ready to use"

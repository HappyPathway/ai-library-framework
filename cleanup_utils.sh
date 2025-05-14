#!/bin/bash
# Script to clean up deprecated utils modules
# This script removes files from the utils directory that have been migrated to ailf

set -e  # Exit on error

BASE_DIR="/workspaces/template-python-dev"
UTILS_DIR="$BASE_DIR/utils"
BACKUP_DIR="$BASE_DIR/utils_backup_$(date +%Y%m%d_%H%M%S)"

# Create backup directory if it doesn't exist
mkdir -p "$BACKUP_DIR"

# Copy all files to backup directory first
echo "Creating backup of utils directory at $BACKUP_DIR"
cp -r "$UTILS_DIR"/* "$BACKUP_DIR/"

# Check that the backup was successful
if [ ! "$(ls -A "$BACKUP_DIR")" ]; then
    echo "Error: Backup failed, aborting cleanup"
    exit 1
fi

echo "Backup completed successfully"

# List of modules that have been migrated and can be safely removed
echo "Cleaning up deprecated files..."

# Core modules
if [ -f "$UTILS_DIR/core/logging.py" ] && [ -f "$BASE_DIR/src/ailf/core/logging.py" ]; then
    echo "Removing utils/core/logging.py (migrated to ailf/core/logging.py)"
    rm "$UTILS_DIR/core/logging.py"
fi

if [ -f "$UTILS_DIR/core/monitoring.py" ] && [ -f "$BASE_DIR/src/ailf/core/monitoring.py" ]; then
    echo "Removing utils/core/monitoring.py (migrated to ailf/core/monitoring.py)"
    rm "$UTILS_DIR/core/monitoring.py"
fi

# Cloud modules
if [ -f "$UTILS_DIR/cloud/secrets.py" ] && [ -f "$BASE_DIR/src/ailf/cloud/secrets.py" ]; then
    echo "Removing utils/cloud/secrets.py (migrated to ailf/cloud/secrets.py)"
    rm "$UTILS_DIR/cloud/secrets.py"
fi

if [ -f "$UTILS_DIR/cloud/gcs.py" ] && [ -f "$BASE_DIR/src/ailf/cloud/gcs_storage.py" ]; then
    echo "Removing utils/cloud/gcs.py (migrated to ailf/cloud/gcs_storage.py)"
    rm "$UTILS_DIR/cloud/gcs.py"
fi

# AI modules
if [ -f "$UTILS_DIR/ai/engine.py" ] && [ -f "$BASE_DIR/src/ailf/ai/engine.py" ]; then
    echo "Removing utils/ai/engine.py (migrated to ailf/ai/engine.py)"
    rm "$UTILS_DIR/ai/engine.py"
fi

# Storage modules
if [ -f "$UTILS_DIR/storage/local.py" ] && [ -f "$BASE_DIR/src/ailf/storage/local.py" ]; then
    echo "Removing utils/storage/local.py (migrated to ailf/storage/local.py)"
    rm "$UTILS_DIR/storage/local.py"
fi

if [ -f "$UTILS_DIR/storage/setup.py" ] && [ -f "$BASE_DIR/src/ailf/setup_storage.py" ]; then
    echo "Removing utils/storage/setup.py (migrated to ailf/setup_storage.py)"
    rm "$UTILS_DIR/storage/setup.py"
fi

# Database module
if [ -f "$UTILS_DIR/database.py" ] && [ -f "$BASE_DIR/src/ailf/storage/database.py" ]; then
    echo "Removing utils/database.py (migrated to ailf/storage/database.py)"
    rm "$UTILS_DIR/database.py"
fi

# GitHub client
if [ -f "$UTILS_DIR/github_client.py" ] && [ -f "$BASE_DIR/src/ailf/github_client.py" ]; then
    echo "Removing utils/github_client.py (migrated to ailf/github_client.py)"
    rm "$UTILS_DIR/github_client.py"
fi

# Async tasks
if [ -f "$UTILS_DIR/async_tasks.py" ] && [ -f "$BASE_DIR/src/ailf/async_tasks.py" ]; then
    echo "Removing utils/async_tasks.py (migrated to ailf/async_tasks.py)"
    rm "$UTILS_DIR/async_tasks.py"
fi

# Base MCP
if [ -f "$UTILS_DIR/base_mcp.py" ] && [ -f "$BASE_DIR/src/ailf/mcp/base.py" ]; then
    echo "Removing utils/base_mcp.py (migrated to ailf/mcp/base.py)"
    rm "$UTILS_DIR/base_mcp.py"
fi

# Messaging modules
if [ -f "$UTILS_DIR/messaging/zmq.py" ] && [ -f "$BASE_DIR/src/ailf/messaging/zmq.py" ]; then
    echo "Removing utils/messaging/zmq.py (migrated to ailf/messaging/zmq.py)"
    rm "$UTILS_DIR/messaging/zmq.py"
fi

if [ -f "$UTILS_DIR/messaging/devices.py" ] && [ -f "$BASE_DIR/src/ailf/messaging/zmq_devices.py" ]; then
    echo "Removing utils/messaging/devices.py (migrated to ailf/messaging/zmq_devices.py)"
    rm "$UTILS_DIR/messaging/devices.py"
fi

if [ -f "$UTILS_DIR/messaging/redis.py" ] && [ -f "$BASE_DIR/src/ailf/messaging/redis.py" ]; then
    echo "Removing utils/messaging/redis.py (migrated to ailf/messaging/redis.py)"
    rm "$UTILS_DIR/messaging/redis.py"
fi

if [ -f "$UTILS_DIR/messaging/mock_redis.py" ] && [ -f "$BASE_DIR/src/ailf/messaging/mock_redis.py" ]; then
    echo "Removing utils/messaging/mock_redis.py (migrated to ailf/messaging/mock_redis.py)"
    rm "$UTILS_DIR/messaging/mock_redis.py"
fi

if [ -f "$UTILS_DIR/messaging/async_redis.py" ] && [ -f "$BASE_DIR/src/ailf/messaging/async_redis.py" ]; then
    echo "Removing utils/messaging/async_redis.py (migrated to ailf/messaging/async_redis.py)"
    rm "$UTILS_DIR/messaging/async_redis.py"
fi

# Workers modules
if [ -f "$UTILS_DIR/workers/celery_app.py" ] && [ -f "$BASE_DIR/src/ailf/workers/celery_app.py" ]; then
    echo "Removing utils/workers/celery_app.py (migrated to ailf/workers/celery_app.py)"
    rm "$UTILS_DIR/workers/celery_app.py"
fi

if [ -f "$UTILS_DIR/workers/tasks.py" ] && [ -f "$BASE_DIR/src/ailf/workers/tasks.py" ]; then
    echo "Removing utils/workers/tasks.py (migrated to ailf/workers/tasks.py)"
    rm "$UTILS_DIR/workers/tasks.py"
fi

# Clean up empty directories
find "$UTILS_DIR" -type d -empty -delete

echo "Cleanup completed successfully."
echo "A backup of the original utils directory is available at $BACKUP_DIR"

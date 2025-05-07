#!/bin/bash
# filepath: /workspaces/template-python-dev/setup/dev_environment_setup.sh
# Development environment setup script for Redis, Celery, and other dependencies

# Exit on error
set -e

echo "Setting up development environment..."

# Check Python version
python_version=$(python3 --version 2>&1 | sed 's/Python //')
python_major=$(echo $python_version | cut -d. -f1)
python_minor=$(echo $python_version | cut -d. -f2)

if [ "$python_major" -lt 3 ] || [ "$python_major" -eq 3 -a "$python_minor" -lt 12 ]; then
    echo "Error: This project requires Python 3.12 or higher"
    echo "Current version: $python_version"
    exit 1
fi

echo "Python version $python_version is compatible"

# Check if Redis is installed
if ! command -v redis-server &> /dev/null; then
    echo "Installing Redis..."
    if [ -f /etc/debian_version ]; then
        # Debian/Ubuntu
        sudo apt-get update
        sudo apt-get install -y redis-server
    elif [ -f /etc/redhat-release ]; then
        # RHEL/CentOS/Fedora
        sudo yum install -y redis
    elif [[ "$OSTYPE" == "darwin"* ]]; then
        # macOS
        brew install redis
    else
        echo "Unsupported OS for automatic Redis installation. Please install Redis manually."
        exit 1
    fi
fi

# Start Redis if not running
if ! pgrep redis-server > /dev/null; then
    echo "Starting Redis server..."
    redis-server --daemonize yes
fi

# Create Python virtual environment if it doesn't exist
if [ ! -d "venv" ]; then
    echo "Creating Python virtual environment..."
    python -m venv venv
fi

# Activate virtual environment
source venv/bin/activate

# Install requirements
echo "Installing Python dependencies..."
pip install -r requirements.txt

# Install development tools
echo "Installing development tools..."
pip install -r requirements/dev.txt

# Create necessary directories
echo "Creating necessary directories..."
mkdir -p logs
mkdir -p data/local_storage

echo "Setting up environment variables..."
# Copy example environment file if no .env exists
if [ ! -f ".env" ]; then
    cp .env.example .env
    echo "Created .env file from example. Please update with your settings."
fi

echo "Testing setup..."
# Simple test to verify Redis is working
python -c "import redis; r = redis.Redis(); r.ping()" && echo "Redis is working correctly!" || echo "Redis connection failed!"

# Test Celery
echo "Testing Celery configuration..."
python -c "from utils.workers.celery_app import app; print(f'Celery configured with broker: {app.conf.broker_url}')"

echo "Setup complete!"
echo ""
echo "To start a Celery worker, run:"
echo "celery -A utils.workers.celery_app worker --loglevel=INFO"
echo ""
echo "To run with auto-reload during development, install watchdog and run:"
echo "pip install watchdog"
echo "watchmedo auto-restart --directory=./ --pattern=*.py --recursive -- celery -A utils.workers.celery_app worker --loglevel=INFO"
echo ""
echo "Happy developing!"

#!/bin/bash
set -e

# Get parameters
INSTALL_REDIS=${INSTALLREDIS:-"true"}
REQUIRED_PYTHON_VERSION=${PYTHONVERSION:-"3.12"}
SETUP_VENV=${SETUPVENV:-"true"}

# Setup directories for consistency
WORKSPACE_DIR="/workspaces"
PROJECT_DIR="${WORKSPACE_DIR}/template-python-dev"
LOGS_DIR="${PROJECT_DIR}/logs"
DATA_DIR="${PROJECT_DIR}/data/local_storage"

echo "Python Development Environment Setup Feature activated!"
echo "Redis installation: $INSTALL_REDIS"
echo "Required Python version: $REQUIRED_PYTHON_VERSION"
echo "Setup virtual environment: $SETUP_VENV"

# Check Python version
PYTHON_VERSION=$(python3 --version | awk '{print $2}')
PYTHON_MAJOR=$(echo $PYTHON_VERSION | cut -d. -f1)
PYTHON_MINOR=$(echo $PYTHON_VERSION | cut -d. -f2)
REQUIRED_MAJOR=$(echo $REQUIRED_PYTHON_VERSION | cut -d. -f1)
REQUIRED_MINOR=$(echo $REQUIRED_PYTHON_VERSION | cut -d. -f2)

echo "Checking Python version..."
echo "Found Python $PYTHON_VERSION"
echo "Required Python $REQUIRED_PYTHON_VERSION"

if [ "$PYTHON_MAJOR" -lt "$REQUIRED_MAJOR" ] || ([ "$PYTHON_MAJOR" -eq "$REQUIRED_MAJOR" ] && [ "$PYTHON_MINOR" -lt "$REQUIRED_MINOR" ]); then
    echo "Error: This project requires Python $REQUIRED_PYTHON_VERSION or higher."
    echo "Current version: $PYTHON_VERSION"
    exit 1
fi
echo "Python version $PYTHON_VERSION is compatible."

# Install Redis if requested
if [ "$INSTALL_REDIS" = "true" ]; then
    echo "Installing Redis..."
    if command -v apt-get &> /dev/null; then
        echo "Attempting Redis installation for Debian/Ubuntu..."
        apt-get update
        apt-get install -y redis-server
    elif command -v yum &> /dev/null; then
        echo "Attempting Redis installation for RHEL/CentOS/Fedora..."
        yum install -y redis
    elif command -v brew &> /dev/null; then
        echo "Attempting Redis installation for macOS..."
        brew install redis
    else
        echo "Unsupported OS for automatic Redis installation. Please install Redis manually."
        exit 1
    fi

    # Start Redis
    echo "Starting Redis server..."
    redis-server --daemonize yes
    sleep 2
    
    # Verify Redis is running
    if redis-cli ping | grep -q "PONG"; then
        echo "Redis server is running."
    else
        echo "Failed to start Redis server. Please check your Redis installation."
    fi
fi

# Create directories
echo "Creating necessary directories..."
mkdir -p "${LOGS_DIR}"
mkdir -p "${DATA_DIR}"

# Setup virtual environment if requested
if [ "$SETUP_VENV" = "true" ]; then
    VENV_DIR="${PROJECT_DIR}/venv"
    echo "Setting up virtual environment at $VENV_DIR..."
    
    if [ ! -d "$VENV_DIR" ]; then
        python3 -m venv "$VENV_DIR"
        echo "Virtual environment created at $VENV_DIR"
    else
        echo "Virtual environment already exists at $VENV_DIR"
    fi
    
    # Install dependencies
    echo "Installing Python dependencies..."
    source "${VENV_DIR}/bin/activate"
    
    if [ -f "${PROJECT_DIR}/requirements.txt" ]; then
        pip install -r "${PROJECT_DIR}/requirements.txt"
        echo "Installed dependencies from requirements.txt"
    else
        echo "Warning: requirements.txt not found at ${PROJECT_DIR}/requirements.txt"
    fi
    
    # Install dev requirements
    DEV_REQUIREMENTS="${PROJECT_DIR}/.devcontainer/requirements/dev.txt"
    if [ -f "$DEV_REQUIREMENTS" ]; then
        pip install -r "$DEV_REQUIREMENTS"
        echo "Installed development dependencies"
    else
        echo "Warning: Development requirements not found at $DEV_REQUIREMENTS"
    fi
    
    deactivate
fi

# Setup environment file
ENV_FILE="${PROJECT_DIR}/.env"
ENV_EXAMPLE_FILE="${PROJECT_DIR}/.env.example"

if [ ! -f "$ENV_FILE" ] && [ -f "$ENV_EXAMPLE_FILE" ]; then
    cp "$ENV_EXAMPLE_FILE" "$ENV_FILE"
    echo "Created .env file from example. Please update with your settings."
elif [ -f "$ENV_FILE" ]; then
    echo ".env file already exists."
else
    echo "Warning: .env.example not found. Cannot create .env file."
fi

echo "Python Development Environment Setup complete!"

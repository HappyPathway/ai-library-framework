#!/usr/bin/env bash
# filepath: /workspaces/template-python-dev/dev_setup.sh

# Exit on error
set -e

# Create virtual environment if it doesn't exist
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python -m venv venv
fi

# Activate virtual environment
source venv/bin/activate

# Upgrade pip
pip install --upgrade pip

# Install the package in development mode with all extras
echo "Installing ailf package in development mode with all extras..."
pip install -e ".[all,dev]"

echo -e "\nDevelopment environment setup complete!"
echo "To activate the virtual environment, run: source venv/bin/activate"

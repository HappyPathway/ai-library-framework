#!/bin/bash
# Script to build comprehensive documentation for the project

set -e

# Move to the project root directory
cd "$(dirname "$0")/.."
ROOT_DIR=$(pwd)

echo "Building documentation from $ROOT_DIR"

# Create virtual environment if it doesn't exist
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
source venv/bin/activate

# Ensure necessary dependencies are installed
pip install -r requirements.txt
pip install sphinx sphinx-markdown-builder myst-parser

# Generate the API structure
echo "Generating API documentation structure..."
python docs/source/api_structure_updated.py

# Build HTML documentation
echo "Building HTML documentation..."
cd docs
make html

echo "Documentation build complete. HTML output is in docs/build/html/"
echo "To view the documentation, open docs/build/html/index.html in a web browser"

# Deactivate virtual environment
deactivate

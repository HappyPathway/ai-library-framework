#!/bin/bash

# Clear VS Code Python extension caches
echo "Clearing Python extension caches..."
rm -rf ~/.vscode-server/data/User/globalStorage/ms-python.*

# Create a clean __pycache__ to ensure Python rebuilds byte-compiled files
find /workspaces/template-python-dev -name "__pycache__" -exec rm -rf {} +

echo "Cache cleared. Please reload VS Code window."

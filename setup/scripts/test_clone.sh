#!/bin/bash
# Test script to manually trigger repository cloning

echo "Testing repository clone script..."
SCRIPT_PATH="/workspaces/template-python-dev/setup/scripts/clone_repositories.sh"

# Check if script exists
if [ ! -f "$SCRIPT_PATH" ]; then
    echo "ERROR: Clone script not found at $SCRIPT_PATH"
    exit 1
fi

# Execute the script
echo "Executing clone script..."
bash "$SCRIPT_PATH"

# Check results
echo -e "\nVerifying repositories..."
REPO_DIR="/workspaces/template-python-dev/repositories"

if [ -d "$REPO_DIR/kagent" ]; then
    echo "✅ kagent repository found"
else
    echo "❌ kagent repository not found"
fi

if [ -d "$REPO_DIR/a2a" ]; then
    echo "✅ A2A repository found"
else
    echo "❌ A2A repository not found"
fi

echo -e "\nRepository clone test complete!"

#!/bin/bash
# Restart the Python Language Server to apply new linting settings

echo "Restarting Python Language Server..."

# Attempt to restart the language server via various methods
if command -v code >/dev/null 2>&1; then
    echo "Using VS Code CLI to reload window..."
    code --reload-window
else
    echo "VS Code CLI not available. Press Ctrl+Shift+P in VS Code and type 'Developer: Reload Window'"
    echo "Then press Ctrl+Shift+P again and type 'Python: Restart Language Server'"
fi

echo "To verify the changes:"
echo "1. Open a Python file with unused imports"
echo "2. No warnings should appear for unused imports"
echo "3. If warnings still appear, try running the command again or restart VS Code"

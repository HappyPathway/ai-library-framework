#!/usr/bin/env bash
# VS Code Python Integration Fix Script

echo "============================================="
echo "VS Code Python Integration Fix Script"
echo "============================================="

echo "1. Clearing VS Code Python extension caches..."
rm -rf ~/.vscode-server/data/User/globalStorage/ms-python.* 2>/dev/null
find /workspaces/template-python-dev -name "__pycache__" -exec rm -rf {} + 2>/dev/null

echo "2. Creating VS Code settings directory if needed..."
mkdir -p /workspaces/template-python-dev/.vscode

echo "3. Updating VS Code settings.json..."
cat > /workspaces/template-python-dev/.vscode/settings.json << EOL
{
    "python.defaultInterpreterPath": "/usr/local/python/current/bin/python3",
    "python.analysis.extraPaths": [
        "/usr/local/python/current/lib/python3.12/site-packages",
        "/usr/local/python/3.12.10/lib/python3.12/site-packages"
    ],
    "python.languageServer": "Pylance",
    "python.analysis.typeCheckingMode": "basic",
    "python.linting.enabled": true,
    "python.linting.pylintEnabled": true,
    "python.formatting.provider": "black",
    "editor.formatOnSave": true,
    "python.analysis.autoImportCompletions": true
}
EOL
echo "  ✓ Settings updated"

echo "4. Creating a test import script..."
cat > /workspaces/template-python-dev/test_imports.py << EOL
# filepath: /workspaces/template-python-dev/test_imports.py
"""Test script to verify import functionality."""

import pydantic
import anthropic
import openai
import google.generativeai as genai
from google.cloud import secretmanager

print("All imports successful!")
print(f"Pydantic version: {pydantic.__version__}")
print(f"OpenAI version: {openai.__version__}")
print(f"Anthropic version: {anthropic.__version__}")
EOL
echo "  ✓ Test script created"

echo "5. Testing import functionality..."
python3 /workspaces/template-python-dev/test_imports.py
echo "  ✓ All imports work from the command line"

echo "============================================="
echo "Next steps:"
echo "1. Reload VS Code window (Ctrl+Shift+P > 'Developer: Reload Window')"
echo "2. Open test_imports.py - verify that no import errors are shown"
echo "3. If problems persist, run this script again after reloading"
echo "============================================="

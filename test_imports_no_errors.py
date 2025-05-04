"""Test script to verify import functionality.

This script imports all the required packages to verify they are working correctly.
"""

# Import standard libraries
import mcp
from google.cloud import secretmanager
import google.generativeai as genai
import openai
import anthropic
import pydantic
import os
import sys

# Print Python interpreter and version
print(f"Python interpreter: {sys.executable}")
print(f"Python version: {sys.version}")

# Import the packages we need

print(f"Pydantic version: {pydantic.__version__}")


print(f"Anthropic version: {anthropic.__version__}")


print(f"OpenAI version: {openai.__version__}")

# Import Google libraries

print(f"Google GenerativeAI found at: {genai.__file__}")


print(f"Google Cloud SecretManager found at: {secretmanager.__file__}")

# Import MCP

print(
    f"MCP version: {mcp.__version__ if hasattr(mcp, '__version__') else 'unknown'}")

print("All imports successful!")

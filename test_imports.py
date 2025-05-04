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

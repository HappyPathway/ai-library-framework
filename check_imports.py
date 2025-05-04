#!/usr/bin/env python3
"""Test imports to verify packages are correctly recognized by VS Code."""

import anthropic
import google.generativeai
import openai
import pydantic
from google.cloud import secretmanager

print("All imports successful!")
print(f"Pydantic version: {pydantic.__version__}")
print(f"OpenAI version: {openai.__version__}")
print(f"Anthropic version: {anthropic.__version__}")

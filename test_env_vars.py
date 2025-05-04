#!/usr/bin/env python
"""
Test script to verify that all required environment variables are set.
"""

import os
import sys

# List of required environment variables
required_vars = [
    "OPENAI_API_KEY",
    "GEMINI_API_KEY",
    "ANTHROPIC_API_KEY",
    "GITHUB_TOKEN",
    "GOOGLE_CLOUD_PROJECT",
    "GOOGLE_APPLICATION_CREDENTIALS",
    "GCS_BUCKET_NAME",
    "ENVIRONMENT",
    "LOGFIRE_API_KEY"
]

# Check each variable
print("Checking environment variables...\n")
all_set = True
results = []

for var in required_vars:
    value = os.environ.get(var)
    if value:
        # Mask the value for security if it's an API key or token
        if "KEY" in var or "TOKEN" in var:
            display_value = value[:4] + "..." + \
                value[-4:] if len(value) > 8 else "***"
        elif "CREDENTIALS" in var:
            display_value = value
        else:
            display_value = value
        results.append(f"✅ {var} is set: {display_value}")
    else:
        results.append(f"❌ {var} is NOT set")
        all_set = False

# Print results
for result in results:
    print(result)

print("\nSummary:")
if all_set:
    print("✅ All required environment variables are set.")
    sys.exit(0)
else:
    print("❌ Some required environment variables are missing.")
    sys.exit(1)

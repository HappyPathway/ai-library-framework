#!/usr/bin/env python
"""
Test script to verify that the AI Engine is functioning properly.
"""

import asyncio

from utils.ai_engine import AIEngine


async def test_ai_engine():
    """Test the AI Engine module."""
    try:
        print("Initializing AIEngine...")
        engine = AIEngine(
            feature_name="env_test",
            model_name="openai:gpt-3.5-turbo",
            provider="openai",
            instructions="You are a helpful assistant."
        )

        print("AIEngine initialized successfully!")

        # Optional: Uncomment to test actual API call
        # print("\nTesting API call with simple prompt...")
        # result = await engine.generate_text("Hello! What day is it today?")
        # print(f"Response: {result}")

        return True

    except Exception as e:
        print(f"❌ Error initializing AIEngine: {e}")
        return False

if __name__ == "__main__":
    success = asyncio.run(test_ai_engine())
    if success:
        print("\n✅ AIEngine test passed: Successfully initialized AIEngine module")
    else:
        print("\n❌ AIEngine test failed: Could not initialize AIEngine module")

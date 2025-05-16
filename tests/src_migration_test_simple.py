"""
Simple Migration Test Script for src-based layout.

This script tests the migrated tooling module and schema files 
without importing from the main AILF package.
"""

import asyncio
import sys
import os
import uuid
from typing import List, Dict, Any, Optional

# Add the src directory to Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "src")))

def run_test():
    """Run migration tests by manually importing the specific modules."""
    print("Running simple migration tests...")
    print("=" * 50)
    
    # Test schemas import
    try:
        print("\nTesting Schema Import:")
        # Import directly from the file
        sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "src", "ailf", "schemas")))
        from tooling import ToolDescription
        
        # Create a test tool description
        tool_desc = ToolDescription(
            name="test_tool",
            description="A test tool",
            categories=["testing", "validation"],
            keywords=["test", "check"]
        )
        
        print(f"Created ToolDescription with name: {tool_desc.name}")
        print(f"Generated ID: {tool_desc.id}")
        print(f"Categories: {tool_desc.categories}")
        print("Schema import and usage successful!")
    except Exception as e:
        print(f"Schema import failed: {e}")
    
    # Test tooling manager and selector
    try:
        print("\nTesting Tooling Import:")
        sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "src", "ailf", "tooling")))
        from manager import ToolManager
        from selector import ToolSelector
        
        print(f"- ToolManager imported: {ToolManager.__name__}")
        print(f"- ToolSelector imported: {ToolSelector.__name__}")
        print("Tooling import successful!")
    except Exception as e:
        print(f"Tooling import failed: {e}")
        
    # Test AI Engine
    try:
        print("\nTesting AI Engine Import:")
        sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "src", "ailf", "ai")))
        from engine import AIEngine, AIEngineError
        
        print(f"- AIEngine imported: {AIEngine.__name__}")
        print(f"- AIEngineError imported: {AIEngineError.__name__}")
        print("AI Engine import successful!")
    except Exception as e:
        print(f"AI Engine import failed: {e}")
        
    print("=" * 50)
    print("Migration test completed!")

if __name__ == "__main__":
    run_test()

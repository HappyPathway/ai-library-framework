"""
Migration Test Script for src-based layout.

This script tests basic functionality of the migrated modules
to ensure they are working correctly in the src-based layout.
"""

import asyncio
import sys
import os
import importlib

# Add the src directory to Python path to ensure the modules can be imported
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "src")))

# We need to create a simple script that tests only the modules we've migrated
# without depending on modules that have not been migrated yet.

# Import specific modules directly
from ailf.schemas.tooling import ToolDescription
from ailf.tooling.manager import ToolManager
from ailf.tooling.selector import ToolSelector

def test_imports():
    """Test importing modules from the src layout."""
    print("Testing imports from src layout:")
    print(f"- ToolManager imported: {ToolManager.__name__}")
    print(f"- ToolSelector imported: {ToolSelector.__name__}")
    print(f"- ToolDescription imported: {ToolDescription.__name__}")
    
    # Try importing AIEngine separately
    print("Attempting to import AIEngine...")
    try:
        from ailf.ai.engine import AIEngine
        print(f"- AIEngine imported: {AIEngine.__name__}")
    except ImportError as e:
        print(f"- AIEngine import failed: {str(e)}")
        
    print("All available imports successful!")

async def test_tool_registration():
    """Test basic tool registration functionality."""
    print("\nTesting tool registration...")
    
    # Create a tool manager
    manager = ToolManager()
    
    # Define a simple tool
    async def simple_tool(text: str) -> str:
        return f"Processed: {text}"
    
    # Create a tool description
    desc = ToolDescription(
        name="simple_processor",
        description="Processes text by adding a prefix"
    )
    
    # Register the tool
    try:
        manager.register_tool(desc, simple_tool)
        print(f"Registered tool with name: {desc.name}")
        
        # Check if the tool was registered
        print(f"Available tools: {manager.tool_names}")
        return True
    except Exception as e:
        print(f"Tool registration error: {e}")
        return False

def test_schemas():
    """Test schema creation."""
    print("\nTesting schema creation...")
    tool_desc = ToolDescription(
        name="test_tool",
        description="A test tool",
        categories=["testing", "validation"],
        keywords=["test", "check"]
    )
    print(f"Created ToolDescription with name: {tool_desc.name}")
    print(f"Generated ID: {tool_desc.id}")
    print(f"Categories: {tool_desc.categories}")
    return True

async def main():
    """Run all tests."""
    print("Running migration tests...")
    print("=" * 50)
    
    # Test imports
    test_imports()
    
    # Test tool registration
    await test_tool_registration()
    
    # Test schemas
    test_schemas()
    
    print("=" * 50)
    print("All tests completed!")

if __name__ == "__main__":
    asyncio.run(main())

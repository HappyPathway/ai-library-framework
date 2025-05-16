"""
Test script for the documentation.py module.

This script demonstrates that the documentation.py module works by:
1. Starting the MCP server in the background
2. Using the get_documentation function to fetch documentation for a standard Python module
3. Displaying the results
"""
import asyncio
import json
from pydantic import BaseModel
from typing import Dict, Any

# Import the module we want to test
from src.ailf.documentation import start_server, DocumentationResult


async def test_documentation_module():
    """Run a test of the documentation module."""
    # Start the server in the background
    server_task = asyncio.create_task(start_server(port=8765))
    
    # Give the server a moment to start up
    await asyncio.sleep(2)
    
    print("🚀 Documentation server started on port 8765")
    
    # Create a client to connect to the server
    import aiohttp
    
    async with aiohttp.ClientSession() as session:
        # Try to get documentation for a well-known module like 'json'
        url = "http://localhost:8765/get_documentation"
        payload = {"object_name": "json"}
        
        print(f"📝 Requesting documentation for '{payload['object_name']}' module...")
        
        try:
            async with session.post(url, json=payload) as response:
                if response.status == 200:
                    result = await response.json()
                    
                    # Print the documentation result in a readable format
                    print("\n✅ Documentation retrieved successfully!")
                    print("\n== Documentation Summary ==")
                    print(f"Module: {result['object_name']}")
                    print(f"Type: {result['object_type']}")
                    print(f"Summary: {result['summary']}")
                    
                    if result.get('docstring'):
                        print(f"\nDocstring: {result['docstring'][:200]}...")  # Show first 200 chars
                    
                    methods = result.get('methods', [])
                    if methods:
                        print(f"\nMethods ({len(methods)} total): {', '.join(methods[:5])}...")
                    
                    attributes = result.get('attributes', {})
                    if attributes:
                        print(f"\nAttributes ({len(attributes)} total): {list(attributes.keys())[:5]}")
                else:
                    print(f"❌ Error: Server returned status {response.status}")
                    print(await response.text())
        except Exception as e:
            print(f"❌ Error connecting to server: {str(e)}")
        
        # Now try getting documentation for a specific function
        payload = {"object_name": "json.loads"}
        
        print(f"\n📝 Requesting documentation for '{payload['object_name']}' function...")
        
        try:
            async with session.post(url, json=payload) as response:
                if response.status == 200:
                    result = await response.json()
                    
                    # Print the documentation result in a readable format
                    print("\n✅ Documentation retrieved successfully!")
                    print("\n== Documentation Summary ==")
                    print(f"Function: {result['object_name']}")
                    print(f"Type: {result['object_type']}")
                    print(f"Summary: {result['summary']}")
                    
                    if result.get('signature'):
                        print(f"Signature: {result['signature']}")
                    
                    if result.get('docstring'):
                        print(f"\nDocstring: {result['docstring'][:200]}...")  # Show first 200 chars
                else:
                    print(f"❌ Error: Server returned status {response.status}")
                    print(await response.text())
        except Exception as e:
            print(f"❌ Error connecting to server: {str(e)}")
    
    # Stop the server
    server_task.cancel()
    try:
        await server_task
    except asyncio.CancelledError:
        print("\n🛑 Server stopped")


if __name__ == "__main__":
    try:
        asyncio.run(test_documentation_module())
        print("\n✨ Test completed successfully")
    except KeyboardInterrupt:
        print("\n🛑 Test interrupted by user")
    except Exception as e:
        print(f"\n❌ Test failed with error: {str(e)}")

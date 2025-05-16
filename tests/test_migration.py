"""
Test script to verify that migration to src-based layout was successful.
This script attempts to import key components from the new structure.
"""

import sys
import os


def test_imports():
    """Test importing key components from the migrated modules."""
    successful_imports = []
    failed_imports = []
    
    # Test one import at a time
    components_to_test = [
        # Main components
        "from ailf import AIEngine, BaseMCP, Context",
        "from ailf import TaskManager, TaskStatus",
        
        # Agent components
        "from ailf import Agent, AgentConfig, AgentStatus",
        
        # AI components
        "from ailf import create_ai_engine, OpenAIEngine",
        "from ailf import AIRequest, AIResponse, AIEngineConfig",
        
        # Cloud components
        "from ailf import get_secrets_manager, GCSStorage",
        
        # Memory components
        "from ailf import Memory, InMemory, FileMemory",
        "from ailf import ShortTermMemory, LongTermMemory",
        
        # Storage components
        "from ailf import LocalStorage, DatabaseStorage",
        
        # Core utilities
        "from ailf import setup_logging, setup_monitoring",
        
        # Messaging components 
        "from ailf import RedisClient, RedisPubSub",
        "from ailf import ZMQPublisher, ZMQSubscriber",
        "from ailf import WebSocketClient, WebSocketServer",
        
        # Cognition components
        "from ailf import ReActProcessor, TaskPlanner",
        "from ailf import PromptTemplateV1, PromptLibrary",
    ]
    
    print("Testing imports from migrated modules...")
    print("=" * 50)
    
    # Let's test first import specifically
    print("Testing individual imports:")
    
    try:
        # First, try importing the base module
        import ailf
        print("✅ import ailf")
        
        # Next, try a simple import from a known module
        from ailf.schemas.ai import AIRequest
        print("✅ from ailf.schemas.ai import AIRequest")
        
        # Try the core logging module specifically
        from ailf.core.logging import setup_logging
        print("✅ from ailf.core.logging import setup_logging")
        
        # Try accessing if there's a cloud.logging module by mistake
        try:
            import ailf.cloud.logging
            print("❓ ailf.cloud.logging exists!")
        except ImportError as e:
            print(f"❌ import ailf.cloud.logging - {e}")
            
    except Exception as e:
        import traceback
        print(f"Error during basic imports: {e}")
        traceback.print_exc()
    
    print("\nNow testing component imports:")
    for import_stmt in components_to_test:
        try:
            exec(import_stmt)
            successful_imports.append(import_stmt)
            print(f"✅ {import_stmt}")
        except ImportError as e:
            failed_imports.append((import_stmt, str(e)))
            print(f"❌ {import_stmt} - {e}")
        except Exception as e:
            import traceback
            failed_imports.append((import_stmt, f"{type(e).__name__}: {str(e)}"))
            print(f"❌ {import_stmt} - Unexpected error: {type(e).__name__}: {str(e)}")
            traceback.print_exc()
    
    print("=" * 50)
    print(f"Summary: {len(successful_imports)} successful, {len(failed_imports)} failed")
    
    if failed_imports:
        print("\nFailed imports:")
        for stmt, error in failed_imports:
            print(f"  - {stmt}: {error}")
    
    return len(failed_imports) == 0


if __name__ == "__main__":
    # Add the src directory to the path for testing
    sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "src")))
    
    # Run the import tests
    success = test_imports()
    
    # Exit with appropriate status code
    sys.exit(0 if success else 1)

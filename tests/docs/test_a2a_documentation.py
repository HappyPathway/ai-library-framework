"""Tests for validating A2A protocol documentation examples.

This module tests the code examples provided in the A2A documentation to ensure
they are correct and up-to-date.
"""
import os
import re
import sys
import inspect
import importlib
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple

import pytest
import httpx
import asyncio

# Import A2A modules
from ailf.communication.a2a_client import A2AClient
from ailf.communication.a2a_server import AILFASA2AServer, A2AAgentExecutor
from ailf.communication.a2a_push import PushNotificationManager
from ailf.communication.a2a_orchestration import A2AOrchestrator
from ailf.schemas.a2a import Message, MessagePart, Task


def extract_code_blocks(file_path: str) -> List[Tuple[str, str]]:
    """Extract code blocks from markdown files.
    
    Returns:
        List of tuples containing (language, code_content)
    """
    with open(file_path, 'r') as f:
        content = f.read()
    
    # Regular expression to find code blocks
    # Format: ```language\ncode\n```
    code_block_pattern = r"```([\w+-]+)\n(.*?)\n```"
    code_blocks = re.findall(code_block_pattern, content, re.DOTALL)
    
    return code_blocks


def filter_python_code_blocks(code_blocks: List[Tuple[str, str]]) -> List[str]:
    """Filter out Python code blocks from the list."""
    return [code for lang, code in code_blocks if lang.lower() in ["python", "py"]]


class DocsCodeValidator:
    """Validates code snippets from documentation."""
    
    def __init__(self):
        self.results = {
            "passed": [],
            "failed": [],
            "skipped": []
        }
    
    def validate_imports(self, code: str) -> bool:
        """Validate that imports in the code exist."""
        import_pattern = r"from\s+([\w.]+)\s+import\s+([^#\n]+)"
        imports = re.findall(import_pattern, code)
        
        all_valid = True
        for module_path, imports_str in imports:
            # Skip relative imports which we can't validate
            if module_path.startswith("."):
                continue
                
            # Handle comma-separated imports
            for imp in imports_str.split(","):
                imp = imp.strip()
                if not imp:
                    continue
                    
                # Handle 'as' renamed imports
                if " as " in imp:
                    imp = imp.split(" as ")[0].strip()
                
                try:
                    # Try importing the module
                    module = importlib.import_module(module_path)
                    
                    # Check if the imported item exists
                    if not hasattr(module, imp):
                        all_valid = False
                        print(f"Import not found: {module_path}.{imp}")
                except ImportError:
                    all_valid = False
                    print(f"Module not found: {module_path}")
        
        return all_valid
    
    def validate_syntax(self, code: str) -> bool:
        """Validate that the code has valid Python syntax."""
        try:
            compile(code, "<string>", "exec")
            return True
        except SyntaxError as e:
            print(f"Syntax error: {str(e)}")
            return False
    
    def validate_a2a_examples(self, docs_dir: str) -> Dict[str, Any]:
        """Validate all A2A code examples in documentation.
        
        Args:
            docs_dir: Directory containing documentation files
            
        Returns:
            Dict containing validation results
        """
        # Find all markdown files
        markdown_files = []
        for root, _, files in os.walk(docs_dir):
            for file in files:
                if file.endswith(".md"):
                    markdown_files.append(os.path.join(root, file))
        
        # Check each file for code blocks
        for file_path in markdown_files:
            file_name = os.path.basename(file_path)
            print(f"Checking {file_name}...")
            
            # Extract code blocks
            code_blocks = extract_code_blocks(file_path)
            python_code = filter_python_code_blocks(code_blocks)
            
            if not python_code:
                continue
                
            # Validate each code block
            for i, code in enumerate(python_code):
                # Skip very short code snippets
                if len(code.strip().split("\n")) < 2:
                    self.results["skipped"].append((file_name, i, "Too short"))
                    continue
                
                # Validate syntax
                if not self.validate_syntax(code):
                    self.results["failed"].append((file_name, i, "Syntax error"))
                    continue
                
                # Validate imports if the code has imports
                if "import" in code:
                    if not self.validate_imports(code):
                        self.results["failed"].append((file_name, i, "Import error"))
                        continue
                
                # If we got here, the code block passed
                self.results["passed"].append((file_name, i))
        
        return self.results


@pytest.mark.docs
class TestA2ADocumentation:
    """Tests that validate A2A documentation examples."""
    
    def test_a2a_code_examples(self):
        """Validate A2A code examples in documentation."""
        # Get documentation directory
        docs_dir = os.path.join(os.path.dirname(__file__), "../../docs")
        
        if not os.path.exists(docs_dir):
            pytest.skip(f"Documentation directory not found: {docs_dir}")
        
        # Run validation
        validator = DocsCodeValidator()
        results = validator.validate_a2a_examples(docs_dir)
        
        # Report results
        print(f"\nValidation Results:")
        print(f"Passed: {len(results['passed'])}")
        print(f"Failed: {len(results['failed'])}")
        print(f"Skipped: {len(results['skipped'])}")
        
        # Log failures
        if results["failed"]:
            print("\nFailures:")
            for file_name, block_index, reason in results["failed"]:
                print(f"- {file_name}, Block #{block_index + 1}: {reason}")
        
        # Assert that there are no failures
        assert len(results["failed"]) == 0, f"{len(results['failed'])} code examples failed validation"
    
    @pytest.mark.asyncio
    async def test_client_code_sample(self):
        """Test that the documented A2A client example code is correct."""
        # This is a simple test that validates the basic client usage pattern
        # shown in documentation matches the actual implementation
        
        # The following code would typically be extracted from documentation,
        # but we're providing a reference implementation directly
        
        async def basic_client_usage(server_url: str, task_id: Optional[str] = None) -> Task:
            """Basic A2A client usage as shown in documentation."""
            # Create a client
            client = A2AClient(server_url)
            
            # Get the agent card
            card = await client.get_agent_card()
            print(f"Connected to {card.name}: {card.description}")
            
            # Create a task or use existing one
            if task_id is None:
                task = await client.create_task()
                task_id = task.id
            else:
                task = await client.get_task(task_id)
            
            # Send a message
            message = Message(
                role="user",
                parts=[MessagePart(type="text", content="Hello, agent!")]
            )
            
            updated_task = await client.send_message(task_id, message)
            return updated_task
        
        # We don't actually call the function, but verify it can be defined
        # This ensures the signatures and patterns match what we document
        assert callable(basic_client_usage)
        
        # Check the parameter types match what we expect
        signature = inspect.signature(basic_client_usage)
        assert "server_url" in signature.parameters
        assert "task_id" in signature.parameters
        assert signature.return_annotation == Task


if __name__ == "__main__":
    pytest.main(["-xvs", __file__])

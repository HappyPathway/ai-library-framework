#!/usr/bin/env python3
"""Script to update Pydantic v1 methods to v2 in A2A client."""

import re

def update_pydantic_methods(file_path):
    """Update Pydantic v1 methods to v2 in the given file."""
    with open(file_path, 'r') as f:
        content = f.read()
    
    # Replace parse_obj with model_validate
    content = re.sub(r'(\w+)\.parse_obj\(', r'\1.model_validate(', content)
    
    # Replace dict() with model_dump()
    content = re.sub(r'\.dict\(\)', r'.model_dump()', content)
    
    # Replace dict(exclude_none=True) with model_dump(exclude_none=True)
    content = re.sub(r'\.dict\(exclude_none=True\)', r'.model_dump(exclude_none=True)', content)
    
    # Replace dict(...) with model_dump(...)
    content = re.sub(r'\.dict\(([^)]*)\)', r'.model_dump(\1)', content)
    
    with open(file_path, 'w') as f:
        f.write(content)

if __name__ == '__main__':
    # Update A2A client
    update_pydantic_methods('/workspaces/template-python-dev/ailf/communication/a2a_client.py')
    print("Updated A2A client")
    
    # Update A2A server
    update_pydantic_methods('/workspaces/template-python-dev/ailf/communication/a2a_server.py')
    print("Updated A2A server")
    
    # Update A2A orchestration
    update_pydantic_methods('/workspaces/template-python-dev/ailf/communication/a2a_orchestration.py')
    print("Updated A2A orchestration")
    
    # Update A2A push
    update_pydantic_methods('/workspaces/template-python-dev/ailf/communication/a2a_push.py')
    print("Updated A2A push")
    
    # Update A2A registry
    update_pydantic_methods('/workspaces/template-python-dev/ailf/communication/a2a_registry.py')
    print("Updated A2A registry")

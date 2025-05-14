#!/usr/bin/env python3
"""Script to update datetime.utcnow() to datetime.now(datetime.UTC)."""

import re

def update_datetime_utcnow(file_path):
    """Update datetime.utcnow() to datetime.now(datetime.UTC) in the given file."""
    with open(file_path, 'r') as f:
        content = f.read()
    
    # Add datetime.UTC import if needed
    if 'import datetime' in content and 'datetime.UTC' not in content:
        content = re.sub(
            r'import datetime',
            'import datetime\nfrom datetime import UTC',
            content
        )
    
    # Replace in classes
    if 'from datetime import datetime' in content and 'from datetime import UTC' not in content:
        content = re.sub(
            r'from datetime import datetime',
            'from datetime import datetime, UTC',
            content
        )
    
    # Replace datetime.datetime.utcnow() with datetime.datetime.now(datetime.UTC)
    content = re.sub(r'datetime\.datetime\.utcnow\(\)', r'datetime.datetime.now(UTC)', content)
    
    # Replace datetime.utcnow() with datetime.now(UTC)
    content = re.sub(r'datetime\.utcnow\(\)', r'datetime.now(UTC)', content)
    
    # Replace default_factory=datetime.utcnow with default_factory=lambda: datetime.now(UTC)
    content = re.sub(
        r'default_factory=datetime\.utcnow', 
        r'default_factory=lambda: datetime.now(UTC)', 
        content
    )
    
    with open(file_path, 'w') as f:
        f.write(content)

if __name__ == '__main__':
    # Update schema files
    update_datetime_utcnow('/workspaces/template-python-dev/ailf/schemas/a2a.py')
    print("Updated A2A schemas")
    
    # Update A2A modules
    update_datetime_utcnow('/workspaces/template-python-dev/ailf/communication/a2a_registry.py')
    print("Updated A2A registry")
    
    update_datetime_utcnow('/workspaces/template-python-dev/ailf/communication/a2a_push.py')
    print("Updated A2A push")
    
    update_datetime_utcnow('/workspaces/template-python-dev/ailf/communication/a2a_orchestration.py')
    print("Updated A2A orchestration")

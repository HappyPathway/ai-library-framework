"""
Script to check if the migrated files exist and are readable.
"""

import os
import glob

def check_files_exist():
    """Check if migrated files exist in the src layout."""
    base_path = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    src_path = os.path.join(base_path, "src")
    
    print(f"Checking migrated files in {src_path}...")
    
    # Define paths to check
    paths_to_check = [
        "src/ailf/ai/engine.py",
        "src/ailf/ai/__init__.py",
        "src/ailf/schemas/tooling.py",
        "src/ailf/tooling/__init__.py",
        "src/ailf/tooling/manager.py",
        "src/ailf/tooling/selector.py"
    ]
    
    found_count = 0
    missing_count = 0
    
    for rel_path in paths_to_check:
        full_path = os.path.join(base_path, rel_path)
        if os.path.exists(full_path):
            print(f"✓ Found: {rel_path}")
            
            # Check if file is readable and has content
            try:
                with open(full_path, 'r') as f:
                    first_line = f.readline().strip()
                    size = os.path.getsize(full_path)
                    print(f"  - Size: {size} bytes")
                    print(f"  - First line: {first_line[:50]}...")
                found_count += 1
            except Exception as e:
                print(f"  - ERROR reading file: {e}")
                missing_count += 1
        else:
            print(f"✗ Missing: {rel_path}")
            missing_count += 1
    
    print(f"\nSummary: Found {found_count} files, {missing_count} missing")
    return found_count, missing_count

if __name__ == "__main__":
    check_files_exist()

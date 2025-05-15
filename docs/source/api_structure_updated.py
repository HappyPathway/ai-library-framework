#!/usr/bin/env python3
"""
Script to generate API documentation markdown files for Sphinx based on the project structure.
This supports both the src-based package structure and legacy modules.
"""

import os
import sys
from pathlib import Path

# Root directories
PROJECT_ROOT = Path('/workspaces/template-python-dev')
SRC_DIR = PROJECT_ROOT / 'src' / 'ailf'  # Main package location in src-based structure
UTILS_DIR = PROJECT_ROOT / 'utils'  # Legacy utils directory
AGENT_DIR = PROJECT_ROOT / 'agent'  # Legacy agent directory 
SCHEMAS_DIR = PROJECT_ROOT / 'schemas'  # Legacy schemas directory
DOCS_API_DIR = PROJECT_ROOT / 'docs' / 'source' / 'api'

# Module groups to create separate directories for
MODULE_GROUPS = [
    'agent', 'ai', 'cloud', 'core', 'messaging', 'schemas', 'storage',
    'mcp', 'communication', 'workers', 'utils'
]

# Templates for markdown files
MODULE_TEMPLATE = """# {module_title}

```{{eval-rst}}
.. automodule:: {module_import_path}
   :members:
   :undoc-members:
   :show-inheritance:
```
"""

INDEX_TEMPLATE = """# {group_title}

```{{toctree}}
:maxdepth: 2

{toc_entries}
```
"""

def ensure_dir(path):
    """Ensure a directory exists, creating it if necessary."""
    os.makedirs(path, exist_ok=True)

def create_module_doc(module_path, relative_path, package_name="ailf", src_based=True):
    """Create documentation file for a module.
    
    Args:
        module_path: Path to the module file
        relative_path: Relative path within the package
        package_name: Base package name
        src_based: Whether the module is in src-based structure
    """
    # Skip __init__.py and __pycache__ directories
    if '__pycache__' in str(module_path) or module_path.name == '__init__.py':
        return None
    
    # Module title is the name without extension
    module_name = module_path.stem
    
    # Convert path for import
    if relative_path:
        import_path = f"{relative_path}/{module_name}"
        module_import_path = f"{package_name}.{relative_path.replace('/', '.')}.{module_name}"
    else:
        import_path = module_name
        module_import_path = f"{package_name}.{module_name}"
    
    # Handle non-src-based imports
    if not src_based:
        module_import_path = import_path.replace('/', '.')
    
    # Clean title
    title = module_name.replace('_', ' ').title()
    
    # Create markdown file path
    doc_path = DOCS_API_DIR / f"{import_path}.md"
    
    # Ensure parent directories exist
    ensure_dir(doc_path.parent)
    
    # Write documentation file with try-except block for autodoc
    with open(doc_path, 'w') as f:
        f.write(MODULE_TEMPLATE.format(
            module_title=title,
            module_import_path=module_import_path
        ))
    
    return doc_path.relative_to(DOCS_API_DIR)

def process_directory(directory, relative_path=None, package_name="ailf", src_based=True):
    """Process a directory to create documentation files for all modules.
    
    Args:
        directory: Directory to process
        relative_path: Relative path within the package
        package_name: Base package name
        src_based: Whether the directory is in src-based structure
    """
    # Skip if not a directory or doesn't exist
    try:
        if not directory.exists() or not directory.is_dir():
            print(f"Skipping non-existent or non-directory path: {directory}")
            return []
    except (FileNotFoundError, PermissionError) as e:
        print(f"Error accessing directory {directory}: {e}")
        return []
    
    # Process Python files
    module_docs = []
    try:
        for item in directory.iterdir():
            try:
                if item.is_file() and item.suffix == '.py':
                    doc_path = create_module_doc(item, relative_path, package_name, src_based)
                    if doc_path:
                        module_docs.append(doc_path)
                elif item.is_dir() and item.name != '__pycache__':
                    # Process subdirectory
                    if relative_path:
                        new_relative = f"{relative_path}/{item.name}"
                    else:
                        new_relative = item.name
                    
                    # Create index file for this subdirectory
                    sub_docs = process_directory(item, new_relative, package_name, src_based)
                    if sub_docs:
                        # Create index file
                        index_path = DOCS_API_DIR / f"{new_relative}.md"
                        with open(index_path, 'w') as f:
                            # Generate TOC entries without .md extension
                            toc_entries = '\n'.join(f"{new_relative}/{doc.stem}" if '/' not in str(doc) else f"{doc.stem}" 
                                                for doc in sub_docs)
                            f.write(INDEX_TEMPLATE.format(
                                group_title=item.name.replace('_', ' ').title(),
                                toc_entries=toc_entries
                            ))
                        # Add relative path properly
                        md_path = Path(f"{new_relative}.md")
                        try:
                            # Try to get a relative path if the file is within the API directory
                            rel_path = md_path.relative_to(DOCS_API_DIR)
                        except ValueError:
                            # If the file is not within the API directory, just use the path as is
                            rel_path = md_path
                        module_docs.append(rel_path)
            except (PermissionError, OSError) as e:
                print(f"Error processing item {item}: {e}")
                continue
    except Exception as e:
        print(f"Error iterating directory {directory}: {e}")
    
    return module_docs

def create_root_index():
    """Create root index file for API documentation."""
    try:
        # Get all subdirectories in the API directory
        dirs = [item for item in DOCS_API_DIR.iterdir() if item.is_dir()]
        
        # Add individual module files
        modules = [item.stem for item in DOCS_API_DIR.iterdir() 
                if item.is_file() and item.suffix == '.md' and item.stem != 'index']
        
        # Sort module groups first, then individual modules
        toc_entries = []
        
        # Add module groups first
        for group in MODULE_GROUPS:
            if any(d.name == group for d in dirs) or f"{group}.md" in [item.name for item in DOCS_API_DIR.iterdir() if item.is_file()]:
                toc_entries.append(group)
        
        # Add remaining files
        for module in sorted(modules):
            if module not in MODULE_GROUPS and module != 'index':
                toc_entries.append(module)
        
        # Write index file
        with open(DOCS_API_DIR / 'index.md', 'w') as f:
            f.write(INDEX_TEMPLATE.format(
                group_title='API Reference',
                toc_entries='\n'.join(toc_entries)
            ))
        
        print(f"Created API root index with {len(toc_entries)} entries")
    except Exception as e:
        print(f"Error creating root index: {e}")
        # Create a basic index file
        try:
            with open(DOCS_API_DIR / 'index.md', 'w') as f:
                f.write(INDEX_TEMPLATE.format(
                    group_title='API Reference',
                    toc_entries='\n'.join(MODULE_GROUPS)
                ))
            print("Created basic API root index as fallback")
        except Exception as e2:
            print(f"Critical error creating even basic index file: {e2}")

def process_non_src_directory(directory, package_name):
    """Process a non-src directory."""
    print(f"Processing non-src directory: {directory} as {package_name}")
    process_directory(directory, None, package_name, src_based=False)

def main():
    """Main function to generate API documentation."""
    print(f"Generating API documentation for src-based structure: {SRC_DIR}")
    
    try:
        # Clear existing API documentation
        if DOCS_API_DIR.exists():
            for item in DOCS_API_DIR.iterdir():
                try:
                    if item.is_file() and item.suffix == '.md':
                        os.remove(item)
                    elif item.is_dir():
                        for subitem in item.glob('**/*.md'):
                            try:
                                os.remove(subitem)
                            except (PermissionError, FileNotFoundError, OSError) as e:
                                print(f"Error removing file {subitem}: {e}")
                except (PermissionError, OSError) as e:
                    print(f"Error processing item {item} during cleanup: {e}")
                    continue
        else:
            ensure_dir(DOCS_API_DIR)
        
        # Create documentation for special module groups first in src structure
        for group in MODULE_GROUPS:
            group_dir = SRC_DIR / group
            try:
                if group_dir.exists():
                    process_directory(group_dir, group)
            except Exception as e:
                print(f"Error processing module group {group}: {e}")
        
        # Process remaining modules in the main package
        if SRC_DIR.exists():
            try:
                module_docs = []
                for item in SRC_DIR.iterdir():
                    try:
                        if item.is_file() and item.suffix == '.py' and item.name != '__init__.py':
                            doc_path = create_module_doc(item, None)
                            if doc_path:
                                module_docs.append(doc_path)
                        elif item.is_dir() and item.name not in MODULE_GROUPS and item.name != '__pycache__':
                            # Process other subdirectories not handled above
                            process_directory(item, item.name)
                    except Exception as e:
                        print(f"Error processing item {item} in src directory: {e}")
            except Exception as e:
                print(f"Error iterating src directory: {e}")
        else:
            print(f"Warning: src directory {SRC_DIR} does not exist")
        
        # Process legacy utils directory if it exists
        if UTILS_DIR.exists():
            try:
                process_non_src_directory(UTILS_DIR, "utils")
            except Exception as e:
                print(f"Error processing utils directory: {e}")
        
        # Process legacy agent directory if it exists
        if AGENT_DIR.exists():
            try:
                process_non_src_directory(AGENT_DIR, "agent")
            except Exception as e:
                print(f"Error processing agent directory: {e}")
            
        # Process legacy schemas directory if it exists
        if SCHEMAS_DIR.exists():
            try:
                process_non_src_directory(SCHEMAS_DIR, "schemas")
            except Exception as e:
                print(f"Error processing schemas directory: {e}")
        
        # Create root index
        try:
            create_root_index()
        except Exception as e:
            print(f"Error creating root index: {e}")
        
        print(f"Generated API documentation files")
    except Exception as e:
        print(f"Critical error in API documentation generation: {e}")

if __name__ == '__main__':
    main()

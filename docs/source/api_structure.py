#!/usr/bin/env python3
"""
Script to generate API documentation markdown files for Sphinx based on the project structure.
This updates the documentation files to match the new src-based package structure.
"""

import os
import sys
from pathlib import Path

# Root directories
PROJECT_ROOT = Path('/workspaces/template-python-dev')
SRC_DIR = PROJECT_ROOT / 'src' / 'ailf'  # Main package location in src-based structure
DOCS_API_DIR = PROJECT_ROOT / 'docs' / 'source' / 'api'

# Module groups to create separate directories for
MODULE_GROUPS = [
    'agent', 'ai', 'cloud', 'core', 'messaging', 'schemas', 'storage',
    'mcp', 'communication', 'workers', 'utils'
]

# Templates for markdown files
MODULE_TEMPLATE = """# {module_title}

```{{eval-rst}}
.. automodule:: ailf.{module_path}
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

def create_module_doc(module_path, relative_path):
    """Create documentation file for a module."""
    # Skip __init__.py and __pycache__ directories
    if '__pycache__' in module_path or module_path.name == '__init__.py':
        return None
    
    # Module title is the name without extension
    module_name = module_path.stem
    
    # Convert path for import
    if relative_path:
        import_path = f"{relative_path}/{module_name}"
    else:
        import_path = module_name
        
    # Clean title
    title = module_name.replace('_', ' ').title()
    
    # Create markdown file
    doc_path = DOCS_API_DIR / f"{import_path}.md"
    
    # Ensure parent directories exist
    ensure_dir(doc_path.parent)
    
    # Write documentation file
    with open(doc_path, 'w') as f:
        f.write(MODULE_TEMPLATE.format(
            module_title=title,
            module_path=import_path
        ))
    
    return doc_path.relative_to(DOCS_API_DIR)

def process_directory(directory, relative_path=None):
    """Process a directory to create documentation files for all modules."""
    # Skip if not a directory
    if not directory.is_dir():
        return []
    
    # Process Python files
    module_docs = []
    for item in directory.iterdir():
        if item.is_file() and item.suffix == '.py':
            doc_path = create_module_doc(item, relative_path)
            if doc_path:
                module_docs.append(doc_path)
        elif item.is_dir() and item.name != '__pycache__':
            # Process subdirectory
            if relative_path:
                new_relative = f"{relative_path}/{item.name}"
            else:
                new_relative = item.name
            
            # Create index file for this subdirectory
            sub_docs = process_directory(item, new_relative)
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
                module_docs.append(Path(f"{new_relative}.md").relative_to(DOCS_API_DIR) if '/' in new_relative else Path(f"{new_relative}.md"))
    
    return module_docs

def create_root_index():
    """Create root index file for API documentation."""
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

def main():
    """Main function to generate API documentation."""
    print(f"Generating API documentation for {SRC_DIR}")
    
    # Clear existing API documentation
    if DOCS_API_DIR.exists():
        for item in DOCS_API_DIR.iterdir():
            if item.is_file() and item.suffix == '.md':
                os.remove(item)
    else:
        ensure_dir(DOCS_API_DIR)
    
    # Create documentation for special module groups first
    for group in MODULE_GROUPS:
        group_dir = SRC_DIR / group
        if group_dir.exists():
            process_directory(group_dir, group)
    
    # Process remaining modules in the main package
    module_docs = []
    for item in SRC_DIR.iterdir():
        if item.is_file() and item.suffix == '.py' and item.name != '__init__.py':
            doc_path = create_module_doc(item, None)
            if doc_path:
                module_docs.append(doc_path)
        elif item.is_dir() and item.name not in MODULE_GROUPS and item.name != '__pycache__':
            # Process other subdirectories not handled above
            process_directory(item, item.name)
    
    # Create root index
    create_root_index()
    
    print(f"Generated {len(module_docs)} API documentation files")

if __name__ == '__main__':
    main()

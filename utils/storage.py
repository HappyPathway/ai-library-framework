"""Local File Storage Manager for Development

This module provides a simple interface for managing local file storage during
development. It includes utilities for creating directories, saving and loading
JSON files, and managing file paths.

Use this module to handle file storage needs in a local development environment.
"""
import os
import json
from pathlib import Path
from typing import Optional, Dict, List, Union

from .logging import setup_logging

# Initialize logger
logger = setup_logging('storage')

class LocalStorage:
    """Local File Storage Manager

The `LocalStorage` class simplifies file storage operations in a local
development environment. It provides methods for:

- Ensuring necessary directories exist.
- Saving and loading JSON files.
- Managing file paths.

This class is ideal for managing data files, documents, and other resources
locally during development.
"""
    
    def __init__(self):
        """Initialize local storage paths."""
        self.base_path = Path(os.path.dirname(__file__)).parent.parent
        self.ensure_directories()
    
    def ensure_directories(self):
        """Ensure Necessary Directories Exist

This method checks for the existence of required directories (e.g., `data`,
`documents`, `profiles`, `strategies`) and creates them if they are missing.

Use this method to prepare the local storage environment before performing
file operations.
"""
        dirs = ['data', 'documents', 'profiles', 'strategies']
        for d in dirs:
            path = self.base_path / d
            path.mkdir(exist_ok=True)
            
    def get_path(self, filename: str) -> Path:
        """Get Full Path for a File

Args:
    filename (str): The name of the file.

Returns:
    Path: The full path to the file within the base directory.

Example:
    ```python
    storage = LocalStorage()
    path = storage.get_path("example.json")
    print(path)  # Outputs: /path/to/base/example.json
    ```
"""
        return self.base_path / filename
    
    def save_json(self, data: Dict, filename: str) -> bool:
        """Save Data as JSON File

This method saves a dictionary as a JSON file in the specified location.

Args:
    data (Dict): The data to save.
    filename (str): The name of the JSON file.

Returns:
    bool: True if the file was saved successfully, False otherwise.

Example:
    ```python
    storage = LocalStorage()
    success = storage.save_json({"key": "value"}, "data.json")
    print(success)  # Outputs: True
    ```
"""
        try:
            path = self.get_path(filename)
            with open(path, 'w') as f:
                json.dump(data, f, indent=2)
            logger.info(f"Saved JSON to {filename}")
            return True
        except Exception as e:
            logger.error(f"Error saving JSON {filename}: {str(e)}")
            return False
            
    def load_json(self, filename: str) -> Optional[Dict]:
        """Load JSON Data from File

This method loads data from a JSON file if it exists.

Args:
    filename (str): The name of the JSON file.

Returns:
    Optional[Dict]: The loaded data as a dictionary, or None if the file does not exist.

Example:
    ```python
    storage = LocalStorage()
    data = storage.load_json("data.json")
    print(data)  # Outputs: {"key": "value"}
    ```
"""
        try:
            path = self.get_path(filename)
            if not path.exists():
                return None
            with open(path) as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Error loading JSON {filename}: {str(e)}")
            return None
            
    def save_text(self, content: str, filename: str) -> bool:
        """Save text content to file."""
        try:
            path = self.get_path(filename)
            with open(path, 'w') as f:
                f.write(content)
            logger.info(f"Saved text to {filename}")
            return True
        except Exception as e:
            logger.error(f"Error saving text {filename}: {str(e)}")
            return False

# Create singleton instance
storage = LocalStorage()
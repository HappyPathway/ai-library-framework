"""Local File Storage Manager for Development

This module provides a simple interface for managing local file storage during
development. It includes utilities for creating directories, saving and loading
JSON files, and managing file paths.

Use this module to handle file storage needs in a local development environment.
"""
import json
import os
import tempfile
from pathlib import Path
from typing import Dict, List, Optional, Union

from .logging import setup_logging

# Initialize logger
logger = setup_logging('storage')

# Initialize module-level variables
_default_storage = None
get_path = None
get_json = None
save_json = None


def get_default_storage_path() -> Path:
    """Get the default storage path.

    Tries to use ~/.template-python-dev, falls back to tempdir if needed.
    """
    try:
        path = Path.home() / '.template-python-dev'
        # Test if we can create/write to this directory
        if not path.exists():
            path.mkdir(parents=True, exist_ok=True)
            # Try writing a test file
            test_file = path / '.test'
            test_file.write_text('')
            test_file.unlink()
        return path
    except (OSError, PermissionError):
        # Fall back to a temporary directory
        import tempfile
        temp_dir = Path(tempfile.gettempdir()) / 'template-python-dev'
        temp_dir.mkdir(parents=True, exist_ok=True)
        return temp_dir


class LocalStorage:
    """Local File Storage Manager

The `LocalStorage` class simplifies file storage operations in a local
development environment. It provides methods for:

- Ensuring necessary directories exist.
- Saving and loading JSON files.
- Managing file paths.

This class is designed to be inherited from for custom storage implementations.
Override the appropriate methods to customize behavior.

Example:
    ```python
    class MyCustomStorage(LocalStorage):
        def __init__(self, custom_config):
            super().__init__(custom_config.path)
            self.custom_setting = custom_config.setting

        def _get_default_dirs(self):
            # Add custom directories
            dirs = super()._get_default_dirs()
            dirs.extend(['custom_dir', 'another_dir'])
            return dirs
    ```
"""

    def __init__(self, base_path: Optional[Union[str, Path]] = None):
        """Initialize local storage paths.

        Args:
            base_path: Optional base path for storage. If not provided,
                      tries user's home directory, falls back to temp dir.
        """
        if base_path is None:
            base_path = self._get_default_base_path()
        self.base_path = Path(base_path)
        self.ensure_directories()

    def _get_default_base_path(self) -> Path:
        """Get the default base path for storage.

        Override this method in subclasses to customize the default base path.

        Returns:
            Path: Default base path
        """
        return get_default_storage_path()

    def _get_default_dirs(self) -> List[str]:
        """Get the list of default directories to create.

        Override this method in subclasses to customize directory structure.

        Returns:
            List[str]: List of directory names to create
        """
        return ['data', 'documents', 'config', 'cache']

    def ensure_directories(self):
        """Initialize and ensure existence of required storage directories.

        Creates a standardized directory structure for storing different types
        of data based on the directories returned by _get_default_dirs().

        This method is called automatically during initialization but can
        be called again to repair the directory structure if needed.

        Example:
            ```python
            storage = LocalStorage()
            storage.ensure_directories()  # Recreate any missing directories
            ```

        Note:
            All directories are created with exist_ok=True to prevent race conditions

        Override _get_default_dirs() instead of this method to customize directories.
        """
        dirs = self._get_default_dirs()
        for d in dirs:
            path = self.base_path / d
            path.mkdir(exist_ok=True)

    def get_path(self, filename: str) -> Path:
        """Get full path for a file in the storage directory.

        Args:
            filename: Name of the file to get path for

        Returns:
            Path: The full absolute path to the file

        Example:
            ```python
            storage = LocalStorage()
            path = storage.get_path("config.json")
            print(path)  # /path/to/base/config.json
            ```

        Note:
            The path is always relative to the base storage directory
        """
        return self.base_path / filename

    def save_json(self, data: Union[Dict, List], filename: str) -> bool:
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
        return self.get_json(filename)

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

    def get_json(self, filename: str) -> Optional[dict]:
        """Load JSON data from file.

        Args:
            filename: Name of the file to load

        Returns:
            Optional[dict]: The loaded JSON data, or None if loading fails
        """
        try:
            path = self.get_path(filename)
            if not path.exists():
                logger.warning(f"File not found: {filename}")
                return None

            with open(path) as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Error loading JSON {filename}: {str(e)}")
            return None

    def save_json(self, data: Union[Dict, List], filename: str) -> bool:
        """Save JSON data to file.

        Args:
            data: The data to save
            filename: Name of the file to save to

        Returns:
            bool: True if successful, False otherwise
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

# Initialize default storage after class definition


def get_default_storage() -> 'LocalStorage':
    """Get or create the default storage instance."""
    global _default_storage, get_path, get_json, save_json
    if _default_storage is None:
        _default_storage = LocalStorage()
        get_path = _default_storage.get_path
        get_json = _default_storage.get_json
        save_json = _default_storage.save_json
    return _default_storage


# Create the default storage instance
_default_storage = get_default_storage()

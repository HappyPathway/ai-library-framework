"""Local File Storage Manager for Development.

This module provides a simple interface for managing local file storage during
development. It includes utilities for creating directories, saving and loading
JSON files, and managing file paths.

Key Features:
- Directory management with automatic creation
- JSON file serialization and deserialization
- Path normalization and validation
- Async and sync operations
- Type-safe file operations

Example:
    >>> from ailf.storage.local import LocalStorage
    >>> 
    >>> # Create a storage manager with a custom base directory
    >>> storage = LocalStorage(base_dir="/tmp/my_app_data")
    >>> 
    >>> # Save some data
    >>> data = {"name": "Example", "value": 42}
    >>> storage.save_json(data, "configs/example.json")
    >>> 
    >>> # Load it back
    >>> loaded = storage.load_json("configs/example.json")
    >>> assert loaded["name"] == "Example"
"""
import asyncio
import json
import os
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

import aiofiles
import aiofiles.os as aios
from pydantic import BaseModel

from ailf.core.logging import setup_logging

# Initialize logger
logger = setup_logging("storage.local")

class StorageError(Exception):
    """Base exception for storage operations."""
    pass


class FileConfig(BaseModel):
    """Configuration for file operations."""
    
    create_dirs: bool = True
    """Automatically create directories if they don't exist."""
    
    overwrite: bool = True
    """Overwrite existing files (if False, raise error when file exists)."""


class LocalStorage:
    """Local file system storage manager."""
    
    def __init__(
        self,
        base_dir: Optional[Union[str, Path]] = None,
        config: Optional[FileConfig] = None
    ):
        """Initialize the storage manager.
        
        Args:
            base_dir: Base directory for storage operations (default: ./data)
            config: Configuration for file operations
        """
        self.base_dir = Path(base_dir) if base_dir else Path.cwd() / "data"
        self.config = config or FileConfig()
        
        # Create base directory if it doesn't exist
        if not self.base_dir.exists():
            logger.info(f"Creating base directory: {self.base_dir}")
            self.base_dir.mkdir(parents=True, exist_ok=True)
            
        logger.debug(f"Initialized LocalStorage with base_dir: {self.base_dir}")
    
    def _get_full_path(self, rel_path: Union[str, Path]) -> Path:
        """Get absolute path from relative path.
        
        Args:
            rel_path: Path relative to base_dir
            
        Returns:
            Absolute path
        """
        if isinstance(rel_path, str):
            rel_path = Path(rel_path)
            
        # If path is already absolute, return it directly
        if rel_path.is_absolute():
            return rel_path
            
        return self.base_dir / rel_path
        
    def _ensure_dir_exists(self, path: Path) -> None:
        """Ensure directory exists, creating it if necessary.
        
        Args:
            path: Directory path
            
        Raises:
            StorageError: If directory couldn't be created
        """
        if not self.config.create_dirs:
            if not path.parent.exists():
                raise StorageError(f"Directory does not exist: {path.parent}")
            return
            
        try:
            path.parent.mkdir(parents=True, exist_ok=True)
        except Exception as e:
            logger.error(f"Failed to create directory {path.parent}: {str(e)}")
            raise StorageError(f"Failed to create directory: {str(e)}") from e
        
    def save_json(
        self,
        data: Any,
        rel_path: Union[str, Path],
        **kwargs
    ) -> Path:
        """Save data as JSON to file.
        
        Args:
            data: Data to save (must be JSON-serializable)
            rel_path: Path relative to base_dir
            **kwargs: Additional options passed to json.dumps()
            
        Returns:
            Absolute path to saved file
            
        Raises:
            StorageError: If file couldn't be saved
        """
        path = self._get_full_path(rel_path)
        self._ensure_dir_exists(path)
        
        # Check if file exists and overwrite setting
        if path.exists() and not self.config.overwrite:
            raise StorageError(f"File already exists: {path}")
        
        try:
            # Include indentation by default for human-readable JSON
            if "indent" not in kwargs:
                kwargs["indent"] = 2
                
            with open(path, "w") as f:
                json.dump(data, f, **kwargs)
                
            logger.debug(f"Saved JSON to {path}")
            return path
        except Exception as e:
            logger.error(f"Failed to save JSON to {path}: {str(e)}")
            raise StorageError(f"Failed to save JSON: {str(e)}") from e
        
    def load_json(
        self,
        rel_path: Union[str, Path],
        default: Any = None,
        **kwargs
    ) -> Any:
        """Load JSON data from file.
        
        Args:
            rel_path: Path relative to base_dir
            default: Value to return if file doesn't exist
            **kwargs: Additional options passed to json.loads()
            
        Returns:
            Loaded data or default value
            
        Raises:
            StorageError: If file couldn't be loaded
        """
        path = self._get_full_path(rel_path)
        
        if not path.exists():
            logger.debug(f"File not found, returning default: {path}")
            return default
        
        try:
            with open(path, "r") as f:
                data = json.load(f, **kwargs)
                
            logger.debug(f"Loaded JSON from {path}")
            return data
        except Exception as e:
            logger.error(f"Failed to load JSON from {path}: {str(e)}")
            raise StorageError(f"Failed to load JSON: {str(e)}") from e
    
    def file_exists(self, rel_path: Union[str, Path]) -> bool:
        """Check if file exists.
        
        Args:
            rel_path: Path relative to base_dir
            
        Returns:
            True if file exists, False otherwise
        """
        path = self._get_full_path(rel_path)
        return path.exists() and path.is_file()
        
    def save_text(
        self,
        text: str,
        rel_path: Union[str, Path],
        encoding: str = "utf-8"
    ) -> Path:
        """Save text to file.
        
        Args:
            text: Text content to save
            rel_path: Path relative to base_dir
            encoding: Text encoding to use
            
        Returns:
            Absolute path to saved file
            
        Raises:
            StorageError: If file couldn't be saved
        """
        path = self._get_full_path(rel_path)
        self._ensure_dir_exists(path)
        
        # Check if file exists and overwrite setting
        if path.exists() and not self.config.overwrite:
            raise StorageError(f"File already exists: {path}")
        
        try:
            with open(path, "w", encoding=encoding) as f:
                f.write(text)
                
            logger.debug(f"Saved text to {path}")
            return path
        except Exception as e:
            logger.error(f"Failed to save text to {path}: {str(e)}")
            raise StorageError(f"Failed to save text: {str(e)}") from e
        
    def load_text(
        self,
        rel_path: Union[str, Path],
        default: Optional[str] = None,
        encoding: str = "utf-8"
    ) -> Optional[str]:
        """Load text from file.
        
        Args:
            rel_path: Path relative to base_dir
            default: Value to return if file doesn't exist
            encoding: Text encoding to use
            
        Returns:
            Loaded text or default value
            
        Raises:
            StorageError: If file couldn't be loaded
        """
        path = self._get_full_path(rel_path)
        
        if not path.exists():
            logger.debug(f"File not found, returning default: {path}")
            return default
        
        try:
            with open(path, "r", encoding=encoding) as f:
                text = f.read()
                
            logger.debug(f"Loaded text from {path}")
            return text
        except Exception as e:
            logger.error(f"Failed to load text from {path}: {str(e)}")
            raise StorageError(f"Failed to load text: {str(e)}") from e
    
    def list_files(
        self,
        rel_dir: Union[str, Path] = "",
        pattern: str = "*",
        recursive: bool = False
    ) -> List[Path]:
        """List files in directory.
        
        Args:
            rel_dir: Directory path relative to base_dir
            pattern: Glob pattern for filtering files
            recursive: Whether to search recursively
            
        Returns:
            List of file paths (relative to base_dir)
            
        Raises:
            StorageError: If directory couldn't be read
        """
        dir_path = self._get_full_path(rel_dir)
        
        if not dir_path.exists():
            logger.debug(f"Directory not found: {dir_path}")
            return []
        
        try:
            if recursive:
                files = list(dir_path.glob(f"**/{pattern}"))
            else:
                files = list(dir_path.glob(pattern))
                
            # Filter out directories and make paths relative to base_dir
            rel_files = [
                p.relative_to(self.base_dir) for p in files if p.is_file()
            ]
            
            logger.debug(f"Listed {len(rel_files)} files in {dir_path}")
            return rel_files
        except Exception as e:
            logger.error(f"Failed to list files in {dir_path}: {str(e)}")
            raise StorageError(f"Failed to list files: {str(e)}") from e
    
    def delete_file(self, rel_path: Union[str, Path]) -> bool:
        """Delete a file.
        
        Args:
            rel_path: Path relative to base_dir
            
        Returns:
            True if file was deleted, False if it didn't exist
            
        Raises:
            StorageError: If file couldn't be deleted
        """
        path = self._get_full_path(rel_path)
        
        if not path.exists():
            logger.debug(f"File not found, nothing to delete: {path}")
            return False
        
        try:
            path.unlink()
            logger.debug(f"Deleted file: {path}")
            return True
        except Exception as e:
            logger.error(f"Failed to delete file {path}: {str(e)}")
            raise StorageError(f"Failed to delete file: {str(e)}") from e
    
    # Async versions of the core methods
    
    async def async_save_json(
        self,
        data: Any,
        rel_path: Union[str, Path],
        **kwargs
    ) -> Path:
        """Asynchronously save data as JSON to file.
        
        Args:
            data: Data to save (must be JSON-serializable)
            rel_path: Path relative to base_dir
            **kwargs: Additional options passed to json.dumps()
            
        Returns:
            Absolute path to saved file
            
        Raises:
            StorageError: If file couldn't be saved
        """
        path = self._get_full_path(rel_path)
        
        # Ensure directory exists
        if not await aios.path.exists(path.parent):
            if not self.config.create_dirs:
                raise StorageError(f"Directory does not exist: {path.parent}")
            await aios.makedirs(path.parent, exist_ok=True)
        
        # Check if file exists
        if await aios.path.exists(path) and not self.config.overwrite:
            raise StorageError(f"File already exists: {path}")
        
        try:
            # Include indentation by default for human-readable JSON
            if "indent" not in kwargs:
                kwargs["indent"] = 2
                
            json_data = json.dumps(data, **kwargs)
            
            async with aiofiles.open(path, "w") as f:
                await f.write(json_data)
                
            logger.debug(f"Asynchronously saved JSON to {path}")
            return path
        except Exception as e:
            logger.error(f"Failed to save JSON to {path}: {str(e)}")
            raise StorageError(f"Failed to save JSON: {str(e)}") from e
    
    async def async_load_json(
        self,
        rel_path: Union[str, Path],
        default: Any = None,
        **kwargs
    ) -> Any:
        """Asynchronously load JSON data from file.
        
        Args:
            rel_path: Path relative to base_dir
            default: Value to return if file doesn't exist
            **kwargs: Additional options passed to json.loads()
            
        Returns:
            Loaded data or default value
            
        Raises:
            StorageError: If file couldn't be loaded
        """
        path = self._get_full_path(rel_path)
        
        if not await aios.path.exists(path):
            logger.debug(f"File not found, returning default: {path}")
            return default
        
        try:
            async with aiofiles.open(path, "r") as f:
                content = await f.read()
                
            data = json.loads(content, **kwargs)
            logger.debug(f"Asynchronously loaded JSON from {path}")
            return data
        except Exception as e:
            logger.error(f"Failed to load JSON from {path}: {str(e)}")
            raise StorageError(f"Failed to load JSON: {str(e)}") from e

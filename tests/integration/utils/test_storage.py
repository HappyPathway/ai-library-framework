"""Integration tests for storage utilities."""
import os
import json
from pathlib import Path
import pytest
from utils.storage import LocalStorage

@pytest.fixture
def storage():
    """Create test storage instance."""
    storage = LocalStorage()
    return storage

@pytest.fixture
def test_data():
    """Create test data."""
    return {"key": "value", "nested": {"test": True}}

@pytest.fixture
def cleanup():
    """Clean up test files after tests."""
    yield
    # Clean up test files
    test_paths = ['test.json', 'test.txt']
    for path in test_paths:
        try:
            os.remove(path)
        except OSError:
            pass

def test_json_storage_operations(storage, test_data, cleanup):
    """Test JSON file storage operations."""
    # Save JSON file
    success = storage.save_json(test_data, "test.json")
    assert success is True
    
    # Load and verify JSON
    loaded_data = storage.load_json("test.json")
    assert loaded_data == test_data
    
    # Test loading non-existent file
    missing_data = storage.load_json("missing.json")
    assert missing_data is None

def test_text_storage_operations(storage, cleanup):
    """Test text file storage operations."""
    test_content = "Test content\nLine 2"
    
    # Save text file
    success = storage.save_text(test_content, "test.txt")
    assert success is True
    
    # Verify file content
    path = storage.get_path("test.txt")
    with open(path) as f:
        content = f.read()
    assert content == test_content

def test_directory_management(storage):
    """Test directory creation and management."""
    required_dirs = ['data', 'documents', 'profiles', 'strategies']
    
    # Verify directories exist
    for dirname in required_dirs:
        path = storage.base_path / dirname
        assert path.exists()
        assert path.is_dir()
        
    # Test creating directories again (should not raise errors)
    storage.ensure_directories()

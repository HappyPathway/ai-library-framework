"""
Unit tests for AILF-Kagent memory bridge.

These tests verify that memory can be shared between AILF and Kagent components.
"""

import pytest
import asyncio
import json
import os
from typing import Dict, Any
from unittest.mock import AsyncMock, patch, MagicMock
import tempfile

# Import Kagent components
from kagent.memory.base import BaseMemory

# Import AILF components
from ailf.memory import MemoryManager as AILFMemory

# Import adapter components
from ailf_kagent.adapters.memory import AILFMemoryBridge, SharedMemoryManager


class TestAILFMemoryBridge:
    """Test suite for AILFMemoryBridge"""

    @pytest.fixture
    def ailf_memory_mock(self):
        """Create a mock AILF MemoryManager for testing"""
        mock = AsyncMock(spec=AILFMemory)
        
        # Configure methods
        mock.get = AsyncMock()
        mock.set = AsyncMock()
        mock.delete = AsyncMock()
        mock.get_all = AsyncMock(return_value={"key1": "value1", "key2": "value2"})
        mock.clear = AsyncMock()
        mock.exists = AsyncMock()
        
        return mock

    @pytest.fixture
    def memory_bridge(self, ailf_memory_mock):
        """Create an AILFMemoryBridge with a mocked AILF memory"""
        with patch('ailf_kagent.adapters.memory.AILFMemory', return_value=ailf_memory_mock):
            bridge = AILFMemoryBridge(namespace="test_namespace")
            # Directly assign the mock to ensure it's used
            bridge.ailf_memory = ailf_memory_mock
            return bridge

    def test_bridge_initialization(self):
        """Test that the memory bridge initializes correctly"""
        with patch('ailf_kagent.adapters.memory.AILFMemory') as mock_memory:
            bridge = AILFMemoryBridge(namespace="test_namespace")
            
            # Verify AILFMemory was initialized with correct namespace
            mock_memory.assert_called_once_with(namespace="test_namespace")
            assert bridge.namespace == "test_namespace"

    @pytest.mark.asyncio
    async def test_get_method(self, memory_bridge, ailf_memory_mock):
        """Test that get method delegates to AILF memory"""
        ailf_memory_mock.get.return_value = "test_value"
        
        result = await memory_bridge.get("test_key")
        
        ailf_memory_mock.get.assert_called_once_with("test_key")
        assert result == "test_value"

    @pytest.mark.asyncio
    async def test_set_method(self, memory_bridge, ailf_memory_mock):
        """Test that set method delegates to AILF memory"""
        await memory_bridge.set("test_key", "test_value")
        
        ailf_memory_mock.set.assert_called_once_with("test_key", "test_value")

    @pytest.mark.asyncio
    async def test_delete_method(self, memory_bridge, ailf_memory_mock):
        """Test that delete method delegates to AILF memory"""
        await memory_bridge.delete("test_key")
        
        ailf_memory_mock.delete.assert_called_once_with("test_key")

    @pytest.mark.asyncio
    async def test_get_all_method(self, memory_bridge, ailf_memory_mock):
        """Test that get_all method delegates to AILF memory"""
        result = await memory_bridge.get_all()
        
        ailf_memory_mock.get_all.assert_called_once()
        assert result == {"key1": "value1", "key2": "value2"}

    @pytest.mark.asyncio
    async def test_clear_method(self, memory_bridge, ailf_memory_mock):
        """Test that clear method delegates to AILF memory"""
        await memory_bridge.clear()
        
        ailf_memory_mock.clear.assert_called_once()

    @pytest.mark.asyncio
    async def test_exists_method(self, memory_bridge, ailf_memory_mock):
        """Test that exists method delegates to AILF memory"""
        ailf_memory_mock.exists.return_value = True
        
        result = await memory_bridge.exists("test_key")
        
        ailf_memory_mock.exists.assert_called_once_with("test_key")
        assert result is True


class TestSharedMemoryManager:
    """Test suite for SharedMemoryManager"""

    @pytest.fixture
    def shared_memory_manager(self):
        """Create a SharedMemoryManager for testing with mocked components"""
        with patch('ailf_kagent.adapters.memory.AILFMemoryBridge') as mock_bridge, \
             patch('ailf_kagent.adapters.memory.AILFMemory') as mock_memory:
            
            manager = SharedMemoryManager(namespace="shared_test")
            # Keep references to the mocks
            manager._mock_bridge = mock_bridge.return_value
            manager._mock_memory = mock_memory.return_value
            return manager

    def test_manager_initialization(self, shared_memory_manager):
        """Test that the manager initializes both memory systems"""
        assert shared_memory_manager.namespace == "shared_test"
        assert shared_memory_manager.kagent_memory == shared_memory_manager._mock_bridge
        assert shared_memory_manager.ailf_memory == shared_memory_manager._mock_memory

    @pytest.mark.asyncio
    async def test_sync_method(self, shared_memory_manager):
        """Test the sync method (currently a placeholder)"""
        # Currently sync is just a placeholder, but test it for coverage
        await shared_memory_manager.sync()
        # No assertions needed since the method is a placeholder

    @pytest.mark.asyncio
    async def test_import_from_json(self, shared_memory_manager):
        """Test importing memory from a JSON file"""
        # Create a temporary JSON file for testing
        test_data = {"key1": "value1", "key2": {"nested": "value2"}}
        
        with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".json") as temp_file:
            json.dump(test_data, temp_file)
            temp_path = temp_file.name
        
        try:
            # Mock the set method on kagent_memory
            shared_memory_manager.kagent_memory.set = AsyncMock()
            
            # Import from the file
            await shared_memory_manager.import_from_json(temp_path)
            
            # Verify both keys were imported
            assert shared_memory_manager.kagent_memory.set.call_count == 2
            # Check that set was called with the correct data
            shared_memory_manager.kagent_memory.set.assert_any_call("key1", "value1")
            shared_memory_manager.kagent_memory.set.assert_any_call("key2", {"nested": "value2"})
        finally:
            # Clean up the temporary file
            os.unlink(temp_path)

    @pytest.mark.asyncio
    async def test_export_to_json(self, shared_memory_manager):
        """Test exporting memory to a JSON file"""
        # Mock get_all to return test data
        test_data = {"key1": "value1", "key2": {"nested": "value2"}}
        shared_memory_manager.kagent_memory.get_all = AsyncMock(return_value=test_data)
        
        # Create a temp file path
        with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as temp_file:
            temp_path = temp_file.name
        
        try:
            # Export to the file
            await shared_memory_manager.export_to_json(temp_path)
            
            # Verify the file was written with correct content
            with open(temp_path, "r") as f:
                saved_data = json.load(f)
                assert saved_data == test_data
        finally:
            # Clean up the temporary file
            os.unlink(temp_path)

    @pytest.mark.asyncio
    async def test_export_error_handling(self, shared_memory_manager):
        """Test error handling during export"""
        # Mock get_all to raise an exception
        shared_memory_manager.kagent_memory.get_all = AsyncMock(side_effect=Exception("Test error"))
        
        # Export should raise RuntimeError
        with pytest.raises(RuntimeError) as excinfo:
            await shared_memory_manager.export_to_json("/nonexistent/path/file.json")
        
        # Verify error message
        assert "Failed to export memory" in str(excinfo.value)

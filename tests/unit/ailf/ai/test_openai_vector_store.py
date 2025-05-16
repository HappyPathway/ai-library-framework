"""Unit tests for OpenAI Vector Store API integration.

This module tests the OpenAI Vector Store API functionality in the OpenAIEngine class.
"""
import pytest
import os
from typing import List, Dict, Any
from unittest.mock import patch, MagicMock, AsyncMock

from ailf.ai.openai_engine import OpenAIEngine
from ailf.schemas.vector_store import (
    VectorStore, VectorStoreSearchResponse, VectorStoreFile, 
    VectorStoreDeleted, VectorStoreSearchResult
)


@pytest.fixture
def mock_openai_client():
    """Create a mock OpenAI client for testing."""
    mock_client = MagicMock()
    
    # Setup vector store mocks
    mock_client.vector_stores = MagicMock()
    mock_client.vector_stores.create = AsyncMock()
    mock_client.vector_stores.retrieve = AsyncMock()
    mock_client.vector_stores.list = AsyncMock()
    mock_client.vector_stores.delete = AsyncMock()
    mock_client.vector_stores.search = AsyncMock()
    
    # Setup vector store files mocks
    mock_client.vector_stores.files = MagicMock()
    mock_client.vector_stores.files.upload_and_poll = AsyncMock()
    mock_client.vector_stores.files.delete = AsyncMock()
    
    return mock_client


@pytest.fixture
def openai_engine(mock_openai_client):
    """Create an instance of OpenAIEngine with a mock client."""
    with patch('ailf.ai.openai_engine.AsyncOpenAI', return_value=mock_openai_client):
        engine = OpenAIEngine(
            api_key="test_api_key",
            model="test-model",
            config={"log_requests": False}
        )
        engine.client = mock_openai_client
        return engine


@pytest.fixture
def sample_vector_store():
    """Sample vector store data."""
    return {
        "id": "vs_abc123",
        "object": "vector_store",
        "created_at": 1656114926,
        "name": "Test Vector Store",
        "description": "A test vector store",
        "metadata": {"purpose": "testing"}
    }


@pytest.mark.asyncio
async def test_create_vector_store(openai_engine, mock_openai_client, sample_vector_store):
    """Test creating a new vector store."""
    # Setup mock response
    mock_response = MagicMock()
    mock_response.model_dump.return_value = sample_vector_store
    mock_openai_client.vector_stores.create.return_value = mock_response
    
    # Test creating a vector store
    name = "Test Vector Store"
    description = "A test vector store"
    metadata = {"purpose": "testing"}
    
    result = await openai_engine.create_vector_store(
        name=name, 
        description=description,
        metadata=metadata
    )
    
    # Verify call parameters
    mock_openai_client.vector_stores.create.assert_called_once_with(
        name=name,
        description=description,
        metadata=metadata
    )
    
    # Verify result
    assert isinstance(result, VectorStore)
    assert result.id == "vs_abc123"
    assert result.name == name
    assert result.description == description
    assert result.metadata == metadata


@pytest.mark.asyncio
async def test_get_vector_store(openai_engine, mock_openai_client, sample_vector_store):
    """Test retrieving a vector store by ID."""
    # Setup mock response
    mock_response = MagicMock()
    mock_response.model_dump.return_value = sample_vector_store
    mock_openai_client.vector_stores.retrieve.return_value = mock_response
    
    # Test retrieving a vector store
    vector_store_id = "vs_abc123"
    result = await openai_engine.get_vector_store(vector_store_id)
    
    # Verify call
    mock_openai_client.vector_stores.retrieve.assert_called_once_with(vector_store_id)
    
    # Verify result
    assert isinstance(result, VectorStore)
    assert result.id == vector_store_id
    assert result.name == "Test Vector Store"


@pytest.mark.asyncio
async def test_list_vector_stores(openai_engine, mock_openai_client):
    """Test listing vector stores."""
    # Setup mock response
    mock_response = MagicMock()
    mock_response.data = [
        MagicMock(model_dump=MagicMock(return_value={
            "id": "vs_1",
            "object": "vector_store",
            "created_at": 1656114926,
            "name": "First Store"
        })),
        MagicMock(model_dump=MagicMock(return_value={
            "id": "vs_2",
            "object": "vector_store",
            "created_at": 1656114950,
            "name": "Second Store"
        }))
    ]
    mock_openai_client.vector_stores.list.return_value = mock_response
    
    # Test listing vector stores
    result = await openai_engine.list_vector_stores(limit=10)
    
    # Verify call
    mock_openai_client.vector_stores.list.assert_called_once_with(limit=10)
    
    # Verify result
    assert isinstance(result, list)
    assert len(result) == 2
    assert all(isinstance(item, VectorStore) for item in result)
    assert result[0].id == "vs_1"
    assert result[1].id == "vs_2"


@pytest.mark.asyncio
async def test_delete_vector_store(openai_engine, mock_openai_client):
    """Test deleting a vector store."""
    # Setup mock response
    mock_response = MagicMock()
    mock_response.model_dump.return_value = {
        "id": "vs_abc123",
        "object": "vector_store.deleted",
        "deleted": True
    }
    mock_openai_client.vector_stores.delete.return_value = mock_response
    
    # Test deleting a vector store
    vector_store_id = "vs_abc123"
    result = await openai_engine.delete_vector_store(vector_store_id)
    
    # Verify call
    mock_openai_client.vector_stores.delete.assert_called_once_with(vector_store_id)
    
    # Verify result
    assert isinstance(result, VectorStoreDeleted)
    assert result.id == vector_store_id
    assert result.deleted is True


@pytest.mark.asyncio
async def test_search_vector_store(openai_engine, mock_openai_client):
    """Test searching a vector store."""
    # Setup mock response
    mock_result1 = MagicMock(model_dump=MagicMock(return_value={
        "id": "file_chunk_1",
        "score": 0.95,
        "text": "Python is a popular language for AI",
        "metadata": {"source": "doc1"},
        "file_id": "file_1"
    }))
    mock_result2 = MagicMock(model_dump=MagicMock(return_value={
        "id": "file_chunk_2",
        "score": 0.85,
        "text": "Machine learning is part of AI",
        "metadata": {"source": "doc2"},
        "file_id": "file_2"
    }))
    
    mock_response = MagicMock()
    mock_response.data = [mock_result1, mock_result2]
    mock_openai_client.vector_stores.search.return_value = mock_response
    
    # Test searching a vector store
    vector_store_id = "vs_abc123"
    query = "AI programming"
    limit = 2
    result = await openai_engine.search_vector_store(
        vector_store_id=vector_store_id,
        query=query,
        limit=limit
    )
    
    # Verify call
    mock_openai_client.vector_stores.search.assert_called_once_with(
        vector_store_id=vector_store_id,
        query=query,
        limit=limit
    )
    
    # Verify result
    assert isinstance(result, list)
    assert len(result) == 2
    assert all(isinstance(item, VectorStoreSearchResult) for item in result)
    assert result[0].text == "Python is a popular language for AI"
    assert result[0].score == 0.95
    assert result[1].text == "Machine learning is part of AI"


@pytest.mark.asyncio
async def test_upload_vector_store_file(openai_engine, mock_openai_client, tmp_path):
    """Test uploading a file to a vector store."""
    # Create a temporary test file
    test_file = tmp_path / "test_file.txt"
    test_file.write_text("This is a test file")
    
    # Setup mock response
    mock_response = MagicMock()
    mock_response.model_dump.return_value = {
        "id": "file_abc123",
        "object": "vector_store.file",
        "created_at": 1656114926,
        "vector_store_id": "vs_abc123",
        "filename": "test_file.txt",
        "purpose": "vector_store",
        "bytes": 19,
        "status": "processed",
        "metadata": {"source": "test"}
    }
    mock_openai_client.vector_stores.files.upload_and_poll.return_value = mock_response
    
    # Test uploading a file
    vector_store_id = "vs_abc123"
    metadata = {"source": "test"}
    
    with patch('builtins.open', create=True) as mock_open:
        mock_file = MagicMock()
        mock_open.return_value.__enter__.return_value = mock_file
        
        result = await openai_engine.upload_vector_store_file(
            vector_store_id=vector_store_id,
            file_path=str(test_file),
            metadata=metadata
        )
        
        # Verify file was opened
        mock_open.assert_called_once_with(str(test_file), "rb")
        
        # Verify API call
        mock_openai_client.vector_stores.files.upload_and_poll.assert_called_once_with(
            vector_store_id=vector_store_id,
            file=mock_file,
            purpose="vector_store",
            metadata=metadata,
            timeout=300.0
        )
    
    # Verify result
    assert isinstance(result, VectorStoreFile)
    assert result.id == "file_abc123"
    assert result.vector_store_id == vector_store_id
    assert result.filename == "test_file.txt"


@pytest.mark.asyncio
async def test_delete_vector_store_file(openai_engine, mock_openai_client):
    """Test deleting a file from a vector store."""
    # Setup mock response
    mock_response = MagicMock()
    mock_response.model_dump.return_value = {
        "id": "file_abc123",
        "object": "vector_store.file.deleted",
        "deleted": True
    }
    mock_openai_client.vector_stores.files.delete.return_value = mock_response
    
    # Test deleting a file
    vector_store_id = "vs_abc123"
    file_id = "file_abc123"
    result = await openai_engine.delete_vector_store_file(
        vector_store_id=vector_store_id,
        file_id=file_id
    )
    
    # Verify call
    mock_openai_client.vector_stores.files.delete.assert_called_once_with(
        vector_store_id=vector_store_id,
        file_id=file_id
    )
    
    # Verify result
    assert isinstance(result, dict)
    assert result["id"] == file_id
    assert result["deleted"] is True


@pytest.mark.asyncio
async def test_error_handling(openai_engine, mock_openai_client):
    """Test error handling in vector store operations."""
    # Setup mock to raise an exception
    mock_openai_client.vector_stores.create.side_effect = Exception("API error")
    
    # Test error handling
    with pytest.raises(Exception) as excinfo:
        await openai_engine.create_vector_store(name="Test Store")
    
    assert "API error" in str(excinfo.value)

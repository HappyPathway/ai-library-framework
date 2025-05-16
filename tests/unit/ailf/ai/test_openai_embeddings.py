"""Unit tests for OpenAI Embeddings API integration.

This module tests the OpenAI Embeddings API functionality in the OpenAIEngine class.
"""
import pytest
import os
from typing import List, Dict, Any
from unittest.mock import patch, MagicMock, AsyncMock

from ailf.ai.openai_engine import OpenAIEngine
from ailf.schemas.embedding import CreateEmbeddingResponse, Embedding


@pytest.fixture
def mock_openai_client():
    """Create a mock OpenAI client for testing."""
    mock_client = MagicMock()
    mock_client.embeddings = MagicMock()
    mock_client.embeddings.create = AsyncMock()
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
def sample_embedding_response():
    """Sample response data for embeddings."""
    return {
        "object": "list",
        "data": [
            {
                "object": "embedding",
                "embedding": [0.1, 0.2, 0.3, 0.4, 0.5],
                "index": 0
            }
        ],
        "model": "text-embedding-3-small",
        "usage": {
            "prompt_tokens": 8,
            "total_tokens": 8
        }
    }


@pytest.mark.asyncio
async def test_create_embedding(openai_engine, mock_openai_client, sample_embedding_response):
    """Test creating embeddings for a single text input."""
    # Setup mock response
    mock_response = MagicMock()
    mock_response.model_dump.return_value = sample_embedding_response
    mock_openai_client.embeddings.create.return_value = mock_response

    # Test with a simple input text
    input_text = "Test input"
    response = await openai_engine.create_embedding(input_text)

    # Verify call parameters
    mock_openai_client.embeddings.create.assert_called_once_with(
        input=input_text,
        model="text-embedding-3-small"
    )

    # Verify response parsing
    assert isinstance(response, CreateEmbeddingResponse)
    assert response.model == "text-embedding-3-small"
    assert len(response.data) == 1
    assert response.data[0].embedding == [0.1, 0.2, 0.3, 0.4, 0.5]
    assert response.usage["total_tokens"] == 8


@pytest.mark.asyncio
async def test_create_embedding_with_options(openai_engine, mock_openai_client, sample_embedding_response):
    """Test creating embeddings with custom model and options."""
    # Setup mock response
    mock_response = MagicMock()
    mock_response.model_dump.return_value = sample_embedding_response
    mock_openai_client.embeddings.create.return_value = mock_response

    # Test with custom options
    input_text = "Test input"
    custom_model = "text-embedding-ada-002"  # legacy model
    dimensions = 1024
    encoding_format = "float"
    user = "user-123"

    response = await openai_engine.create_embedding(
        input_text=input_text,
        model=custom_model,
        dimensions=dimensions,
        encoding_format=encoding_format,
        user=user
    )

    # Verify call parameters
    mock_openai_client.embeddings.create.assert_called_once_with(
        input=input_text,
        model=custom_model,
        dimensions=dimensions,
        encoding_format=encoding_format,
        user=user
    )

    assert isinstance(response, CreateEmbeddingResponse)


@pytest.mark.asyncio
async def test_create_embedding_with_list_input(openai_engine, mock_openai_client):
    """Test creating embeddings for a list of texts."""
    # Setup mock response with multiple embeddings
    mock_response = MagicMock()
    mock_response.model_dump.return_value = {
        "object": "list",
        "data": [
            {
                "object": "embedding",
                "embedding": [0.1, 0.2, 0.3],
                "index": 0
            },
            {
                "object": "embedding",
                "embedding": [0.4, 0.5, 0.6],
                "index": 1
            }
        ],
        "model": "text-embedding-3-small",
        "usage": {
            "prompt_tokens": 16,
            "total_tokens": 16
        }
    }
    mock_openai_client.embeddings.create.return_value = mock_response

    # Test with list input
    input_texts = ["First text", "Second text"]
    response = await openai_engine.create_embedding(input_texts)

    # Verify call parameters
    mock_openai_client.embeddings.create.assert_called_once_with(
        input=input_texts,
        model="text-embedding-3-small"
    )

    # Verify response
    assert len(response.data) == 2
    assert response.data[0].embedding == [0.1, 0.2, 0.3]
    assert response.data[1].embedding == [0.4, 0.5, 0.6]


@pytest.mark.asyncio
async def test_batch_create_embeddings(openai_engine, mock_openai_client):
    """Test batch creation of embeddings."""
    # Mock response for single batch
    mock_response = MagicMock()
    mock_response.model_dump.return_value = {
        "object": "list",
        "data": [
            {
                "object": "embedding",
                "embedding": [0.1, 0.2, 0.3],
                "index": 0
            },
            {
                "object": "embedding",
                "embedding": [0.4, 0.5, 0.6],
                "index": 1
            }
        ],
        "model": "text-embedding-3-small",
        "usage": {
            "prompt_tokens": 16,
            "total_tokens": 16
        }
    }
    mock_openai_client.embeddings.create.return_value = mock_response

    # Test with a small batch that doesn't need splitting
    texts = ["Text 1", "Text 2"]
    result = await openai_engine.batch_create_embeddings(texts, batch_size=10)

    # Verify call
    mock_openai_client.embeddings.create.assert_called_once()
    
    # Verify result format
    assert isinstance(result, list)
    assert len(result) == 2
    assert result[0] == [0.1, 0.2, 0.3]
    assert result[1] == [0.4, 0.5, 0.6]


@pytest.mark.asyncio
async def test_batch_create_embeddings_large_batch(openai_engine, mock_openai_client):
    """Test batch creation of embeddings with batching logic."""
    # Create mock responses for multiple batches
    mock_response1 = MagicMock()
    mock_response1.model_dump.return_value = {
        "object": "list",
        "data": [
            {"object": "embedding", "embedding": [0.1, 0.2], "index": 0},
            {"object": "embedding", "embedding": [0.3, 0.4], "index": 1}
        ],
        "model": "text-embedding-3-small",
        "usage": {"prompt_tokens": 10, "total_tokens": 10}
    }
    
    mock_response2 = MagicMock()
    mock_response2.model_dump.return_value = {
        "object": "list",
        "data": [
            {"object": "embedding", "embedding": [0.5, 0.6], "index": 0},
            {"object": "embedding", "embedding": [0.7, 0.8], "index": 1}
        ],
        "model": "text-embedding-3-small",
        "usage": {"prompt_tokens": 10, "total_tokens": 10}
    }
    
    mock_openai_client.embeddings.create.side_effect = [mock_response1, mock_response2]

    # Test with a batch that requires splitting
    texts = ["Text 1", "Text 2", "Text 3", "Text 4"]
    result = await openai_engine.batch_create_embeddings(texts, batch_size=2)

    # Verify multiple calls were made
    assert mock_openai_client.embeddings.create.call_count == 2
    
    # Verify result contains all embeddings
    assert len(result) == 4
    assert result == [[0.1, 0.2], [0.3, 0.4], [0.5, 0.6], [0.7, 0.8]]


@pytest.mark.asyncio
async def test_create_embedding_error_handling(openai_engine, mock_openai_client):
    """Test error handling in create_embedding method."""
    # Setup mock to raise an exception
    mock_openai_client.embeddings.create.side_effect = Exception("API error")

    # Test error handling
    with pytest.raises(Exception) as excinfo:
        await openai_engine.create_embedding("Test input")
    
    assert "API error" in str(excinfo.value)

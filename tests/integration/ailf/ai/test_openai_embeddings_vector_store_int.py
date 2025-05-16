"""Integration tests for OpenAI Embeddings and Vector Store APIs.

This module provides integration tests for OpenAI Embeddings and Vector Store APIs.
These tests require a valid OpenAI API key in the environment.
"""
import os
import pytest
import asyncio
from typing import List, Dict, Any

from ailf.ai.openai_engine import OpenAIEngine
from ailf.schemas.embedding import CreateEmbeddingResponse
from ailf.schemas.vector_store import (
    VectorStore, VectorStoreSearchResult, VectorStoreFile
)


@pytest.fixture
def openai_api_key():
    """Get the OpenAI API key from the environment."""
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        pytest.skip("OPENAI_API_KEY not set in environment")
    return api_key


@pytest.fixture
async def openai_engine(openai_api_key):
    """Create an OpenAIEngine instance for testing."""
    engine = OpenAIEngine(
        api_key=openai_api_key,
        model="gpt-3.5-turbo",
        config={"log_requests": True}
    )
    
    yield engine


@pytest.mark.integration
@pytest.mark.asyncio
async def test_create_embedding(openai_engine):
    """Test creating embeddings with the OpenAI API."""
    # Skip if no API key
    if not os.getenv("OPENAI_API_KEY"):
        pytest.skip("OPENAI_API_KEY not set in environment")
        
    # Test with a simple text
    text = "This is a test for embedding generation."
    embedding_response = await openai_engine.create_embedding(text)
    
    # Validate the response
    assert isinstance(embedding_response, CreateEmbeddingResponse)
    assert embedding_response.model is not None
    assert len(embedding_response.data) == 1
    assert len(embedding_response.data[0].embedding) > 0
    assert embedding_response.usage["total_tokens"] > 0
    
    # Test with multiple texts
    texts = [
        "First test text for embeddings.",
        "Second text for testing embeddings API.",
        "Third example of text for embedding generation."
    ]
    
    batch_embeddings = await openai_engine.batch_create_embeddings(texts)
    
    # Validate batch response
    assert isinstance(batch_embeddings, list)
    assert len(batch_embeddings) == 3
    assert all(isinstance(embedding, list) for embedding in batch_embeddings)
    assert all(len(embedding) > 0 for embedding in batch_embeddings)
    
    # Verify dimensions are consistent
    assert all(len(embedding) == len(batch_embeddings[0]) for embedding in batch_embeddings)


@pytest.mark.integration
@pytest.mark.asyncio
async def test_vector_store_lifecycle(openai_engine, tmp_path):
    """Test the complete vector store lifecycle: create, upload, search, delete."""
    # Skip if no API key
    if not os.getenv("OPENAI_API_KEY"):
        pytest.skip("OPENAI_API_KEY not set in environment")
    
    # Create a vector store
    vector_store = await openai_engine.create_vector_store(
        name="AILF Integration Test Store",
        description="Test vector store for integration testing",
        metadata={"test": "true"}
    )
    
    assert isinstance(vector_store, VectorStore)
    assert vector_store.id is not None
    assert vector_store.name == "AILF Integration Test Store"
    
    try:
        # Create a test file
        test_file_path = tmp_path / "test_data.txt"
        with open(test_file_path, "w") as f:
            f.write("This is test data for vector store integration.\n")
            f.write("AILF provides tools for AI agent development.\n")
            f.write("Vector stores enable semantic search capabilities.\n")
        
        # Upload the file
        uploaded_file = await openai_engine.upload_vector_store_file(
            vector_store_id=vector_store.id,
            file_path=str(test_file_path),
            metadata={"content": "test data"}
        )
        
        assert isinstance(uploaded_file, VectorStoreFile)
        assert uploaded_file.vector_store_id == vector_store.id
        
        # Allow time for processing
        await asyncio.sleep(5)
        
        # Search the vector store
        search_results = await openai_engine.search_vector_store(
            vector_store_id=vector_store.id,
            query="What is AILF?",
            limit=2
        )
        
        assert isinstance(search_results, list)
        assert all(isinstance(result, VectorStoreSearchResult) for result in search_results)
        
        # Delete the file
        delete_file_response = await openai_engine.delete_vector_store_file(
            vector_store_id=vector_store.id,
            file_id=uploaded_file.id
        )
        
        assert delete_file_response["deleted"] is True
        
        # List vector stores
        stores = await openai_engine.list_vector_stores()
        assert isinstance(stores, list)
        assert any(store.id == vector_store.id for store in stores)
        
        # Get vector store by ID
        retrieved_store = await openai_engine.get_vector_store(vector_store.id)
        assert retrieved_store.id == vector_store.id
        
    finally:
        # Clean up
        try:
            delete_response = await openai_engine.delete_vector_store(vector_store.id)
            assert delete_response.deleted is True
        except Exception as e:
            print(f"Error cleaning up vector store: {e}")


if __name__ == "__main__":
    asyncio.run(test_create_embedding(openai_engine))
    asyncio.run(test_vector_store_lifecycle(openai_engine, tmp_path))

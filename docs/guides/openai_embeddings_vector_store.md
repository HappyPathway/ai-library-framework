# OpenAI Embeddings and Vector Store Integration in AILF

This document provides guidance on using OpenAI's Embeddings API and Vector Store API within the AILF framework.

## Overview

AILF's `OpenAIEngine` class integrates with OpenAI's Embeddings API and Vector Store API, providing:

1. **Embeddings Generation**: Convert text to vector representations for semantic search and similarity analysis.
2. **Vector Stores**: Create and manage vector databases that enable efficient semantic search over your data.

## Prerequisites

- An OpenAI API key with access to the Embeddings and Vector Store APIs
- AILF library installed with OpenAI dependencies
- Python 3.8 or higher

## Setup

### Installation

Ensure you have the required dependencies:

```bash
pip install "ailf[openai]"
```

Or install from requirements:

```bash
pip install -e ".[openai]"
```

### Authentication

Set your OpenAI API key as an environment variable:

```bash
export OPENAI_API_KEY="your-api-key"
```

Or load it from a `.env` file using Python:

```python
from dotenv import load_dotenv
load_dotenv()  # loads environment variables from .env file
```

## Using the Embeddings API

### Initializing the OpenAI Engine

```python
from ailf.ai.openai_engine import OpenAIEngine

engine = OpenAIEngine(
    api_key="your-api-key",  # Optional if already in environment
    model="gpt-4o",          # Default model for text generation
    config={
        "temperature": 0.7,
        "max_tokens": 1000
    }
)
```

### Creating Embeddings for a Single Text

```python
import asyncio

async def create_embedding_example():
    # Generate embedding for a single text
    text = "The quick brown fox jumps over the lazy dog"
    response = await engine.create_embedding(text)
    
    # Examine the response
    print(f"Model: {response.model}")
    print(f"Tokens used: {response.usage['total_tokens']}")
    print(f"Embedding dimensions: {len(response.data[0].embedding)}")
    print(f"First 5 values: {response.data[0].embedding[:5]}")

asyncio.run(create_embedding_example())
```

### Creating Embeddings for Multiple Texts

```python
async def create_multiple_embeddings():
    texts = [
        "Machine learning is a field of study that gives computers the ability to learn without being explicitly programmed",
        "Python is an interpreted, high-level, general-purpose programming language",
        "Artificial intelligence is intelligence demonstrated by machines"
    ]
    
    # Using the batch_create_embeddings method
    embeddings = await engine.batch_create_embeddings(texts)
    
    # The result is a list of embedding vectors
    for i, embedding in enumerate(embeddings):
        print(f"Text {i+1} embedding dimensions: {len(embedding)}")

asyncio.run(create_multiple_embeddings())
```

### Creating Embeddings with Custom Parameters

```python
async def custom_embeddings():
    text = "Example text for embeddings"
    
    # Customize the embedding generation
    response = await engine.create_embedding(
        input_text=text,
        model="text-embedding-3-large",  # Larger model for higher quality
        dimensions=256,                  # Custom output dimensions
        encoding_format="float"          # Specify encoding format
    )
    
    print(f"Embedding dimensions: {len(response.data[0].embedding)}")

asyncio.run(custom_embeddings())
```

## Using the Vector Store API

### Creating a Vector Store

```python
async def create_vector_store_example():
    # Create a new vector store
    vector_store = await engine.create_vector_store(
        name="My Knowledge Base",
        description="A vector store for my project's data",
        metadata={"project": "ailf-demo"}
    )
    
    print(f"Created vector store: {vector_store.id}")
    return vector_store

vector_store = asyncio.run(create_vector_store_example())
```

### Uploading Files to a Vector Store

```python
async def upload_file_example(vector_store_id):
    # Path to the file you want to upload
    file_path = "data/documents.txt"
    
    # Upload the file
    file = await engine.upload_vector_store_file(
        vector_store_id=vector_store_id,
        file_path=file_path,
        metadata={"source": "user-documentation"}
    )
    
    print(f"Uploaded file: {file.id}")
    return file

file = asyncio.run(upload_file_example(vector_store.id))
```

### Searching in a Vector Store

```python
async def search_vector_store_example(vector_store_id):
    # Allow time for processing (may be needed for newly uploaded files)
    await asyncio.sleep(5)
    
    # Search the vector store with a query
    results = await engine.search_vector_store(
        vector_store_id=vector_store_id,
        query="What are the key features?",
        limit=5  # Return top 5 matches
    )
    
    print("\nSearch Results:")
    for i, result in enumerate(results):
        print(f"Result {i+1}:")
        print(f"  Score: {result.score}")
        print(f"  Text: {result.text}")
        print()

asyncio.run(search_vector_store_example(vector_store.id))
```

### Managing Vector Stores

```python
async def manage_vector_stores():
    # List all vector stores
    stores = await engine.list_vector_stores(limit=10)
    print(f"Found {len(stores)} vector stores")
    
    for store in stores:
        print(f"- {store.name} (ID: {store.id})")
    
    # Get details of a specific store
    if stores:
        store_id = stores[0].id
        store_details = await engine.get_vector_store(store_id)
        print(f"\nVector store '{store_details.name}':")
        print(f"  Created: {store_details.created_at}")
        print(f"  Description: {store_details.description}")
    
    # Delete a vector store when no longer needed
    if stores:
        delete_response = await engine.delete_vector_store(stores[0].id)
        print(f"Deleted vector store: {delete_response.id}")

asyncio.run(manage_vector_stores())
```

## Complete Example

Here's a complete example showing the entire workflow:

```python
import asyncio
import os
from dotenv import load_dotenv

from ailf.ai.openai_engine import OpenAIEngine


async def vector_store_workflow():
    # Load API key from environment
    load_dotenv()
    api_key = os.getenv("OPENAI_API_KEY")
    
    if not api_key:
        print("Error: OPENAI_API_KEY not found in environment.")
        return
    
    # Initialize the engine
    engine = OpenAIEngine(
        api_key=api_key,
        model="gpt-4o",
        config={"temperature": 0.7}
    )
    
    try:
        # Create a vector store
        print("Creating vector store...")
        vector_store = await engine.create_vector_store(
            name="AILF Knowledge Base",
            description="Vector store for AILF documentation"
        )
        print(f"Created vector store: {vector_store.id}")
        
        # Create sample data file
        file_path = "sample_data.txt"
        with open(file_path, "w") as f:
            f.write("AILF is a Python library for building AI agents.\n")
            f.write("It provides tools for LLM interactions, memory management, and agent communication.\n")
            f.write("The library supports various AI providers including OpenAI and Anthropic.\n")
        
        # Upload the file
        print("Uploading file to vector store...")
        file = await engine.upload_vector_store_file(
            vector_store_id=vector_store.id,
            file_path=file_path
        )
        print(f"Uploaded file: {file.id}")
        
        # Wait for processing
        print("Waiting for file processing...")
        await asyncio.sleep(5)
        
        # Search the vector store
        print("Searching vector store...")
        results = await engine.search_vector_store(
            vector_store_id=vector_store.id,
            query="What AI providers does AILF support?",
            limit=2
        )
        
        print("\nSearch Results:")
        for i, result in enumerate(results):
            print(f"Result {i+1}:")
            print(f"  Score: {result.score}")
            print(f"  Text: {result.text}")
            print()
            
    except Exception as e:
        print(f"Error: {str(e)}")
    finally:
        # Clean up
        print("Cleaning up...")
        try:
            await engine.delete_vector_store(vector_store.id)
            os.remove(file_path)
            print("Vector store and sample file deleted.")
        except Exception as e:
            print(f"Error during cleanup: {str(e)}")


if __name__ == "__main__":
    asyncio.run(vector_store_workflow())
```

## Error Handling and Best Practices

### Error Handling

The `OpenAIEngine` provides built-in error handling with informative messages. For robust applications, wrap API calls in try-except blocks:

```python
try:
    embedding = await engine.create_embedding("Test text")
    # Process the embedding
except Exception as e:
    print(f"Error generating embedding: {e}")
    # Implement fallback behavior
```

### Rate Limiting

OpenAI APIs have rate limits. The `OpenAIEngine` handles basic retries, but for production use:

1. Implement exponential backoff for retries
2. Add delays between batch operations
3. Monitor usage and throttle requests as needed

### Cost Management

Both Embeddings and Vector Store APIs incur costs:

1. Embeddings are charged per token
2. Vector stores incur storage and search costs

Monitor usage through the OpenAI dashboard and implement limits in your code.

## Advanced Usage

### Fine-tuning Embedding Parameters

For optimal performance, adjust embedding parameters based on your use case:

```python
# Higher dimensions for more complex semantic relationships
response = await engine.create_embedding(
    input_text=complex_text,
    model="text-embedding-3-large",
    dimensions=1536
)

# Lower dimensions for faster processing and reduced storage
response = await engine.create_embedding(
    input_text=simple_text,
    model="text-embedding-3-small",
    dimensions=256
)
```

### Vector Store Best Practices

1. **Chunk documents** into smaller sections before uploading for better search results
2. **Use meaningful metadata** to enhance filtering capabilities
3. **Clean and normalize text** before embedding to improve quality
4. **Periodically update** vector stores to reflect changes in your data

## Troubleshooting

### Common Issues and Solutions

1. **Invalid API Key**:
   - Verify the API key is correct
   - Check that the key has access to the Embeddings and Vector Store APIs

2. **Rate Limiting**:
   - Implement progressive backoff
   - Consider using a higher tier OpenAI plan

3. **Poor Search Results**:
   - Improve the quality of input documents
   - Refine search queries
   - Use a more powerful embedding model

4. **File Processing Delays**:
   - Large files may take time to process
   - Implement appropriate waiting mechanisms in production code

## References

- [OpenAI API Documentation](https://platform.openai.com/docs/guides/embeddings)
- [Vector Store API Documentation](https://platform.openai.com/docs/api-reference/vector-stores)
- [AILF Documentation](https://ailf.dev)

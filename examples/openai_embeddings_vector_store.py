#!/usr/bin/env python3
"""
OpenAI Embeddings and Vector Store Example

This example demonstrates how to use the AILF OpenAIEngine for 
generating embeddings and working with vector stores.
"""
import asyncio
import os
from typing import List

from dotenv import load_dotenv

from ailf.ai.openai_engine import OpenAIEngine
from ailf.ai.schemas.embedding import CreateEmbeddingResponse
from ailf.ai.schemas.vector_store import VectorStore, VectorStoreSearchResult


async def embedding_example(engine: OpenAIEngine) -> None:
    """Demonstrate the embeddings functionality."""
    print("\n=== Embeddings Example ===")
    
    # Generate embedding for a single text
    texts = ["The quick brown fox jumps over the lazy dog"]
    
    print(f"Generating embedding for: {texts[0]}")
    response = await engine.create_embedding(texts[0])
    
    print(f"Model: {response.model}")
    print(f"Tokens used: {response.usage['total_tokens']}")
    print(f"Embedding dimensions: {len(response.data[0].embedding)}")
    print(f"First 5 values: {response.data[0].embedding[:5]}")
    
    # Generate embeddings for multiple texts
    texts = [
        "The quick brown fox jumps over the lazy dog",
        "Machine learning is a field of study that gives computers the ability to learn without being explicitly programmed",
        "Python is an interpreted, high-level, general-purpose programming language"
    ]
    
    print(f"\nGenerating embeddings for {len(texts)} texts with batch method")
    embeddings = await engine.batch_create_embeddings(texts)
    
    for i, embedding in enumerate(embeddings):
        print(f"Text {i+1} embedding dimensions: {len(embedding)}")


async def vector_store_example(engine: OpenAIEngine) -> None:
    """Demonstrate the vector store functionality."""
    print("\n=== Vector Store Example ===")
    
    # Create a new vector store
    vector_store = await engine.create_vector_store(
        name="AILF Example Store",
        description="An example vector store for the AILF framework"
    )
    
    print(f"Created vector store: {vector_store.id}")
    
    # Create a sample file for the vector store
    sample_file_path = "sample_data.txt"
    with open(sample_file_path, "w") as f:
        f.write("This is sample text data about artificial intelligence.\n")
        f.write("Machine learning is a subset of artificial intelligence.\n")
        f.write("Python is a popular programming language for AI development.\n")
    
    try:
        # Upload the file to the vector store
        print("Uploading file to vector store...")
        file = await engine.upload_vector_store_file(
            vector_store_id=vector_store.id,
            file_path=sample_file_path
        )
        
        print(f"Uploaded file: {file.id}")
        
        # Wait a moment for processing
        print("Waiting for file processing...")
        await asyncio.sleep(5)
        
        # Search the vector store
        print("Searching vector store...")
        results = await engine.search_vector_store(
            vector_store_id=vector_store.id,
            query="What programming language is used for AI?",
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
            os.remove(sample_file_path)
            print("Vector store and sample file deleted.")
        except Exception as e:
            print(f"Error during cleanup: {str(e)}")


async def main() -> None:
    """Run the OpenAI Embeddings and Vector Store examples."""
    # Load API key from environment
    load_dotenv()
    api_key = os.getenv("OPENAI_API_KEY")
    
    if not api_key:
        print("Error: OPENAI_API_KEY not found in environment.")
        return
    
    # Initialize the OpenAI engine
    engine = OpenAIEngine(
        api_key=api_key,
        model="gpt-4o",
        config={
            "temperature": 0.7,
            "max_tokens": 1000
        }
    )
    
    # Run the examples
    await embedding_example(engine)
    await vector_store_example(engine)


if __name__ == "__main__":
    asyncio.run(main())

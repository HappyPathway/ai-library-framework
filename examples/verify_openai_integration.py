#!/usr/bin/env python3
"""
OpenAI Integration Check Script

This script verifies the OpenAI Embeddings and Vector Store API integration in the AILF framework.
It requires an OpenAI API key in the environment (OPENAI_API_KEY).
"""
import asyncio
import os
import tempfile
from typing import List

from dotenv import load_dotenv

from ailf.ai.openai_engine import OpenAIEngine
from ailf.core.logging import setup_logging


async def verify_openai_integration() -> None:
    """Run a series of checks to verify OpenAI API integration works properly."""
    logger = setup_logging("openai_integration_check")
    logger.info("Starting OpenAI integration verification...")
    
    # Load environment variables
    load_dotenv()
    api_key = os.getenv("OPENAI_API_KEY")
    
    if not api_key:
        logger.error("OPENAI_API_KEY not found in environment")
        print("Error: OPENAI_API_KEY not set. Please set it in your environment or .env file.")
        return
    
    # Initialize the engine
    logger.info("Initializing OpenAI engine...")
    engine = OpenAIEngine(
        api_key=api_key,
        model="gpt-3.5-turbo",
        config={"log_requests": True}
    )
    
    has_error = False
    
    # Check embeddings
    try:
        logger.info("Testing embedding creation...")
        embedding_response = await engine.create_embedding("This is a test for embedding generation.")
        print(f"✓ Created embedding successfully with {len(embedding_response.data[0].embedding)} dimensions")
        
        # Test batch embeddings
        texts = ["First test text", "Second test text", "Third test text"]
        embeddings = await engine.batch_create_embeddings(texts)
        print(f"✓ Created batch embeddings successfully for {len(embeddings)} texts")
        
    except Exception as e:
        has_error = True
        logger.error(f"Embedding test failed: {e}")
        print(f"✗ Embedding test failed: {e}")
    
    # Check vector store
    vector_store_id = None
    file_id = None
    try:
        logger.info("Testing vector store creation...")
        vector_store = await engine.create_vector_store(
            name="AILF Integration Test",
            description="Testing vector store API integration"
        )
        vector_store_id = vector_store.id
        print(f"✓ Created vector store with ID: {vector_store.id}")
        
        # Create temporary file
        with tempfile.NamedTemporaryFile(mode="w+", suffix=".txt", delete=False) as temp_file:
            temp_file_path = temp_file.name
            temp_file.write("This is test content for the vector store API.\n")
            temp_file.write("The AILF framework integrates with OpenAI's vector stores.\n")
            temp_file.write("Vector stores enable semantic search capabilities for AI agents.\n")
        
        # Upload file
        logger.info("Testing file upload to vector store...")
        file = await engine.upload_vector_store_file(
            vector_store_id=vector_store_id,
            file_path=temp_file_path
        )
        file_id = file.id
        print(f"✓ Uploaded file to vector store with ID: {file.id}")
        
        # Wait for processing
        print("Waiting for file processing...")
        await asyncio.sleep(5)
        
        # Test search
        logger.info("Testing vector store search...")
        results = await engine.search_vector_store(
            vector_store_id=vector_store_id,
            query="What are vector stores used for?",
            limit=1
        )
        
        if results:
            print(f"✓ Successfully searched vector store")
            print(f"  Top result (score {results[0].score:.2f}): {results[0].text}")
        else:
            print("✓ Search returned no results (this can happen with new files)")
            
        # Test listing vector stores
        stores = await engine.list_vector_stores(limit=5)
        print(f"✓ Listed vector stores: found {len(stores)} stores")
        
    except Exception as e:
        has_error = True
        logger.error(f"Vector store test failed: {e}")
        print(f"✗ Vector store test failed: {e}")
    
    # Clean up
    try:
        if file_id and vector_store_id:
            logger.info(f"Cleaning up: deleting file {file_id}...")
            await engine.delete_vector_store_file(
                vector_store_id=vector_store_id,
                file_id=file_id
            )
            print(f"✓ Deleted file from vector store")
            
        if vector_store_id:
            logger.info(f"Cleaning up: deleting vector store {vector_store_id}...")
            await engine.delete_vector_store(vector_store_id)
            print(f"✓ Deleted vector store")
            
        # Clean up temporary file
        if 'temp_file_path' in locals():
            os.unlink(temp_file_path)
            
    except Exception as e:
        logger.error(f"Cleanup failed: {e}")
        print(f"✗ Cleanup failed: {e}")
    
    # Final result
    if has_error:
        logger.error("Integration verification completed with errors")
        print("\n❌ Verification completed with some errors. Check logs for details.")
    else:
        logger.info("Integration verification completed successfully")
        print("\n✅ All OpenAI integration tests passed successfully!")
        print("\nThe AILF framework is correctly integrated with:")
        print("  ✓ OpenAI Embeddings API")
        print("  ✓ OpenAI Vector Store API")


if __name__ == "__main__":
    asyncio.run(verify_openai_integration())

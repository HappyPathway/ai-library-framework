"""Task definitions for Celery.

This module defines distributed tasks that can be executed by Celery workers.
Each task should be a standalone function that can be serialized and executed
in a separate process or on a different machine.

Example:
    # Execute a task
    from utils.workers.tasks import process_document
    
    # Run synchronously (for testing)
    result = process_document.delay("doc-123", options={"format": "json"})
    
    # Check status later
    from celery.result import AsyncResult
    task_result = AsyncResult(result.id)
    print(f"Status: {task_result.status}, Result: {task_result.result}")
"""

import time
import traceback
from typing import Any, Dict, List, Optional

from utils.logging import setup_logging
from utils.workers.celery_app import app

logger = setup_logging("celery.tasks")


@app.task(bind=True, name="tasks.process_document")
def process_document(self, document_id: str, options: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """Process a document asynchronously.

    Args:
        document_id: The ID of the document to process
        options: Optional processing options

    Returns:
        Processing results
    """
    start_time = time.time()
    options = options or {}

    logger.info(f"Processing document {document_id} with options: {options}")

    try:
        # Example document processing logic
        # In a real implementation, you would load and process the document

        # Simulate processing time
        time.sleep(2)

        result = {
            "document_id": document_id,
            "status": "success",
            "processing_time": time.time() - start_time,
            "metadata": {
                "word_count": 1000,
                "processed_at": time.time()
            }
        }

        logger.info(f"Successfully processed document {document_id}")
        return result

    except Exception as e:
        logger.error(f"Error processing document {document_id}: {str(e)}")
        logger.error(traceback.format_exc())

        # Store the error in the task result
        self.update_state(
            state="FAILURE",
            meta={
                "document_id": document_id,
                "status": "error",
                "error": str(e),
                "traceback": traceback.format_exc()
            }
        )
        raise


@app.task(bind=True, name="tasks.analyze_content")
def analyze_content(self, content: str, analysis_type: str = "general") -> Dict[str, Any]:
    """Analyze content using AI.

    Args:
        content: The content to analyze
        analysis_type: The type of analysis to perform

    Returns:
        Analysis results
    """
    start_time = time.time()

    logger.info(f"Analyzing content of type {analysis_type}")

    try:
        # For a real implementation, you would integrate with your AI engine
        # Example: from utils.ai_engine import AIEngine

        # Simulate processing time
        time.sleep(3)

        # Example result
        result = {
            "analysis_type": analysis_type,
            "processing_time": time.time() - start_time,
            "results": {
                "sentiment": "positive",
                "key_topics": ["technology", "AI", "development"],
                "summary": "Content discusses advancements in AI technology."
            }
        }

        logger.info(f"Successfully analyzed content")
        return result

    except Exception as e:
        logger.error(f"Error analyzing content: {str(e)}")
        logger.error(traceback.format_exc())

        self.update_state(
            state="FAILURE",
            meta={
                "analysis_type": analysis_type,
                "status": "error",
                "error": str(e),
                "traceback": traceback.format_exc()
            }
        )
        raise

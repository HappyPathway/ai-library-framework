"""
Example demonstrating the Agent Protocol client.

This example shows how to interact with an Agent Protocol compliant service
using the AgentProtocolClient class.

To run this example, make sure you have a compliant server running, or
replace the BASE_URL with an appropriate endpoint.
"""

import argparse
import asyncio
import json
import logging
import sys
from pathlib import Path
from typing import Optional

from utils.messaging.agent_protocol_client import (
    AgentProtocolClient, AgentProtocolError, TaskCreationError
)
from schemas.messaging.agent_protocol import ArtifactType

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


async def run_agent_protocol_example(
    base_url: str,
    input_text: str,
    api_key: Optional[str] = None,
    file_path: Optional[str] = None
):
    """Run an example interaction with an Agent Protocol server.
    
    Args:
        base_url: The base URL of the Agent Protocol server
        input_text: The input text for the task
        api_key: Optional API key for authentication
        file_path: Optional path to a file to upload as an artifact
    """
    try:
        async with AgentProtocolClient(base_url, api_key=api_key) as client:
            logger.info(f"Creating task with input: {input_text}")
            
            # Create a task
            task = await client.create_task(input_text)
            logger.info(f"Task created with ID: {task.task_id}")
            
            # Execute a step
            step_input = "Let's analyze this by breaking it down into steps"
            logger.info(f"Executing step with input: {step_input}")
            
            step = await client.execute_step(task.task_id, step_input)
            logger.info(f"Step executed with ID: {step.step_id}")
            logger.info(f"Step output: {step.output}")
            
            # Upload an artifact if file_path is provided
            if file_path:
                path = Path(file_path)
                if path.exists():
                    logger.info(f"Uploading artifact from {file_path}")
                    upload_response = await client.upload_artifact(
                        task.task_id,
                        step.step_id,
                        path,
                        artifact_type=ArtifactType.FILE
                    )
                    logger.info(f"Artifact uploaded with ID: {upload_response.artifact_id}")
                else:
                    logger.error(f"File not found: {file_path}")
            
            # Get updated task info
            updated_task = await client.get_task(task.task_id)
            logger.info(f"Task status: {updated_task.status}")
            logger.info(f"Number of steps: {len(updated_task.steps)}")
            
            # List all steps
            steps = await client.list_steps(task.task_id)
            logger.info(f"Retrieved {len(steps)} steps")
            
            # Print summary
            logger.info("\nTask Summary:")
            logger.info(f"Task ID: {updated_task.task_id}")
            logger.info(f"Status: {updated_task.status}")
            logger.info(f"Created At: {updated_task.created_at}")
            if updated_task.completed_at:
                logger.info(f"Completed At: {updated_task.completed_at}")

    except TaskCreationError as e:
        logger.error(f"Failed to create task: {e}")
        return 1
    except AgentProtocolError as e:
        logger.error(f"Agent protocol error: {e}")
        return 1
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        return 1
    
    return 0


def main():
    """Main entry point for the example."""
    parser = argparse.ArgumentParser(description="Agent Protocol Client Example")
    parser.add_argument(
        "--base-url", 
        type=str, 
        default="http://localhost:8000",
        help="Base URL for the Agent Protocol server"
    )
    parser.add_argument(
        "--input", 
        type=str, 
        default="Analyze the impact of climate change on agriculture",
        help="Input text for the task"
    )
    parser.add_argument(
        "--api-key", 
        type=str, 
        help="API key for authentication"
    )
    parser.add_argument(
        "--file", 
        type=str, 
        help="Path to a file to upload as an artifact"
    )
    
    args = parser.parse_args()
    
    return asyncio.run(run_agent_protocol_example(
        args.base_url,
        args.input,
        args.api_key,
        args.file
    ))


if __name__ == "__main__":
    sys.exit(main())

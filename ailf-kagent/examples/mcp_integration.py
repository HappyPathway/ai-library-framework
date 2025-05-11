"""
Example demonstrating integration with the Model Context Protocol (MCP) server,
combining AILF's tool capabilities with Kagent's agent orchestration.

This example shows how to:
1. Create AILF tools for document processing
2. Expose them to Kagent via an MCP server
3. Build a Kagent agent that uses these tools
"""

import asyncio
import os
from typing import Dict, List, Optional, Union
from pydantic import BaseModel, Field
import json

# Import AILF components
from ailf.tooling import ToolDescription, ToolManager
from ailf.schemas import BaseSchema

# Import Kagent components 
from kagent.agents import Agent as KAgent
from kagent.schema import AgentResponse

# Import MCP components (assuming a simple implementation for this example)
from mcp.server import MCPServer

# Import the integration adapters
from ailf_kagent.adapters.tools import AILFToolAdapter, AILFToolRegistry
from ailf_kagent.adapters.schemas import SchemaRegistry


#
# Define AILF document processing tools
#

class DocumentInput(BaseModel):
    """Input for document processing tools"""
    document_id: str = Field(..., description="ID of the document to process")
    parameters: Optional[Dict[str, Union[str, int, float, bool]]] = Field(
        default=None, description="Optional processing parameters"
    )


class DocumentSummary(BaseModel):
    """Output from document summarization"""
    summary: str = Field(..., description="Generated summary")
    key_points: List[str] = Field(..., description="Key points extracted")
    word_count: int = Field(..., description="Word count of the summary")


class DocumentMetadata(BaseModel):
    """Output from document metadata extraction"""
    title: str = Field(..., description="Document title")
    author: Optional[str] = Field(None, description="Document author")
    created_date: Optional[str] = Field(None, description="Document creation date")
    modified_date: Optional[str] = Field(None, description="Document last modification date")
    tags: List[str] = Field(default_factory=list, description="Document tags")
    page_count: Optional[int] = Field(None, description="Number of pages")


# Mock document database for the example
DOCUMENTS = {
    "doc1": {
        "content": "This is a sample document about artificial intelligence...",
        "metadata": {
            "title": "Introduction to AI",
            "author": "John Smith",
            "created_date": "2025-01-15",
            "modified_date": "2025-04-22",
            "tags": ["AI", "introduction", "technology"],
            "page_count": 12
        }
    },
    "doc2": {
        "content": "Climate change is affecting global temperatures...",
        "metadata": {
            "title": "Climate Change Report",
            "author": "Maria Rodriguez",
            "created_date": "2024-11-30",
            "modified_date": "2025-03-10",
            "tags": ["climate", "environment", "science"],
            "page_count": 45
        }
    }
}


async def summarize_document(input_data: DocumentInput) -> DocumentSummary:
    """Generate a summary of the document.
    
    In a real implementation, this would use an LLM or specialized
    summarization algorithm.
    """
    doc_id = input_data.document_id
    
    if doc_id not in DOCUMENTS:
        raise ValueError(f"Document with ID {doc_id} not found")
    
    # In a real implementation, we would do actual summarization
    # This is just a mock for the example
    document = DOCUMENTS[doc_id]
    content = document["content"]
    
    # Mock summary generation
    summary = f"Summary of '{document['metadata']['title']}': {content[:50]}..."
    key_points = ["This is a key point", "Another important point"]
    word_count = len(content.split())
    
    return DocumentSummary(
        summary=summary,
        key_points=key_points,
        word_count=word_count
    )


async def extract_metadata(input_data: DocumentInput) -> DocumentMetadata:
    """Extract metadata from the document."""
    doc_id = input_data.document_id
    
    if doc_id not in DOCUMENTS:
        raise ValueError(f"Document with ID {doc_id} not found")
    
    # Extract metadata from the document
    metadata = DOCUMENTS[doc_id]["metadata"]
    
    return DocumentMetadata(**metadata)


def create_mcp_server(tool_registry):
    """Create an MCP server with the registered tools.
    
    In a real implementation, this would create a proper MCP server.
    This is a simplified version for the example.
    """
    server = MCPServer(name="Document Processing Service")
    
    # Register all tools from the registry
    for tool in tool_registry.list_tools():
        server.register_tool(tool)
    
    return server


async def main():
    # Create AILF tools
    summarize_tool = ToolDescription(
        id="summarize-document",
        description="Generate a summary of a document",
        input_schema=DocumentInput,
        output_schema=DocumentSummary,
        function=summarize_document
    )
    
    metadata_tool = ToolDescription(
        id="extract-metadata",
        description="Extract metadata from a document",
        input_schema=DocumentInput,
        output_schema=DocumentMetadata,
        function=extract_metadata
    )
    
    # Create a tool registry
    registry = AILFToolRegistry()
    registry.register(summarize_tool)
    registry.register(metadata_tool)
    
    # Create an MCP server with the tools
    server = create_mcp_server(registry)
    
    # In a real implementation, we would start the server
    # For this example, we'll just print the available tools
    print(f"MCP Server '{server.name}' registered with tools:")
    for tool_id in server.list_tools():
        print(f"- {tool_id}")
    
    # Create a Kagent agent that would use these tools via MCP
    # In a real implementation, the agent would connect to the running server
    agent = KAgent()
    
    # For this example, we'll manually add adapted tools to the agent
    for tool in registry.list_tools():
        adapter = AILFToolAdapter(tool)
        agent.add_tool(adapter)
    
    # Example agent execution
    print("\nExecuting agent query...")
    response = await agent.run("Get me a summary of document doc1")
    print(f"Agent response: {response}")
    
    response = await agent.run("What are the metadata details for document doc2?")
    print(f"Agent response: {response}")


if __name__ == "__main__":
    asyncio.run(main())

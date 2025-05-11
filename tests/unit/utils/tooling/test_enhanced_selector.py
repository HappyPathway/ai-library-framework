"""Tests for the enhanced ailf.tooling.selector component."""
import pytest
import numpy as np
from typing import List, Dict, Any, Optional, Tuple

from ailf.schemas.tooling import ToolDescription
from ailf.tooling.selector_enhanced import ToolSelector

class MockEmbeddingModel:
    """Mock embedding model for testing."""
    
    def __init__(self, embedding_dim: int = 10):
        """
        Initialize mock model.
        
        :param embedding_dim: Dimension of mock embeddings
        """
        self.embedding_dim = embedding_dim
        self.text_to_embedding_map = {}
    
    def get_embedding(self, text: str) -> List[float]:
        """
        Get an embedding for text.
        
        :param text: Input text
        :return: Embedding vector
        """
        # Return a consistent embedding for the same text
        if text not in self.text_to_embedding_map:
            # Generate a deterministic embedding based on text content
            import hashlib
            hash_obj = hashlib.md5(text.encode())
            hash_int = int(hash_obj.hexdigest(), 16)
            
            # Convert hash to a normalized vector
            rng = np.random.RandomState(hash_int)
            vector = rng.rand(self.embedding_dim)
            norm = np.linalg.norm(vector)
            if norm > 0:
                vector = vector / norm  # Normalize to unit vector
            
            self.text_to_embedding_map[text] = vector.tolist()
        
        return self.text_to_embedding_map[text]

class MockRegistryClient:
    """Mock registry client for testing."""
    
    def __init__(self, tools: Optional[List[ToolDescription]] = None):
        """
        Initialize mock client.
        
        :param tools: Optional predefined tools
        """
        self.tools = tools or []
    
    async def discover_tools(
        self,
        query: Optional[str] = None,
        tool_names: Optional[List[str]] = None,
        categories: Optional[List[str]] = None,
        limit: int = 100
    ) -> List[ToolDescription]:
        """
        Mock tool discovery.
        
        :param query: Query string
        :param tool_names: Tool names to filter by
        :param categories: Categories to filter by
        :param limit: Maximum number of tools to return
        :return: List of tool descriptions
        """
        filtered_tools = self.tools
        
        if tool_names:
            filtered_tools = [
                tool for tool in filtered_tools 
                if tool.name in tool_names
            ]
        
        if categories:
            filtered_tools = [
                tool for tool in filtered_tools
                if any(cat in tool.categories for cat in categories)
            ]
        
        # Simple keyword filtering if query is provided
        if query:
            query_lower = query.lower()
            filtered_tools = [
                tool for tool in filtered_tools
                if (
                    query_lower in tool.name.lower() or
                    query_lower in tool.description.lower() or
                    any(query_lower in kw.lower() for kw in tool.keywords)
                )
            ]
        
        return filtered_tools[:limit]

@pytest.fixture
def sample_tools() -> List[ToolDescription]:
    """Create sample tools for testing."""
    return [
        ToolDescription(
            name="calculator",
            description="Performs mathematical calculations",
            categories=["math", "utility"],
            keywords=["calculate", "math", "compute", "arithmetic"],
            usage_examples=["Calculate 2+2", "What is the square root of 16?"]
        ),
        ToolDescription(
            name="weather_lookup",
            description="Gets current weather information for a location",
            categories=["information", "weather"],
            keywords=["weather", "forecast", "temperature", "rain", "humidity"],
            usage_examples=["What's the weather in New York?", "Will it rain tomorrow?"]
        ),
        ToolDescription(
            name="file_search",
            description="Searches for files in the system",
            categories=["system", "utility"],
            keywords=["search", "file", "find", "locate", "document"],
            usage_examples=["Find all PDF files", "Search for documents containing 'budget'"]
        ),
        ToolDescription(
            name="email_sender",
            description="Composes and sends emails",
            categories=["communication", "email"],
            keywords=["email", "send", "compose", "message"],
            usage_examples=["Send an email to John", "Email the team about the meeting"]
        )
    ]

@pytest.fixture
def embedding_model() -> MockEmbeddingModel:
    """Create mock embedding model."""
    return MockEmbeddingModel(embedding_dim=10)

@pytest.fixture
def registry_client(sample_tools) -> MockRegistryClient:
    """Create mock registry client."""
    return MockRegistryClient(tools=sample_tools)

def test_keyword_selection(sample_tools):
    """Test keyword-based tool selection."""
    selector = ToolSelector(selection_strategy="keyword_match")
    
    # Test with weather query
    weather_query = "What's the weather like today?"
    result = selector.select_tool(weather_query, sample_tools)
    assert result[0][0].name == "weather_lookup"  # First result should be weather tool
    assert len(result) == 1  # There should be one result
    
    # Test with math query
    math_query = "Calculate the square root of 16"
    result = selector.select_tool(math_query, sample_tools)
    assert result[0][0].name == "calculator"
    
    # Test with file query
    file_query = "Search for my documents"
    result = selector.select_tool(file_query, sample_tools)
    assert result[0][0].name == "file_search"
    
    # Test with ambiguous query (should return top matches)
    ambiguous_query = "Find information"
    result = selector.select_tool(ambiguous_query, sample_tools, threshold=0.05, top_k=2)
    assert len(result) > 0  # Should return at least one match
    
    # Test with no matching query
    no_match_query = "abcdefghijklmnopqrstuvwxyz"
    result = selector.select_tool(no_match_query, sample_tools)
    assert len(result) == 0  # Should return no matches

@pytest.mark.asyncio
async def test_rag_selection(sample_tools, embedding_model):
    """Test RAG-based tool selection."""
    # Create a selector with RAG strategy
    selector = ToolSelector(selection_strategy="rag", embedding_model=embedding_model)
    
    # Add embeddings to tools
    tools_with_embeddings = []
    for tool in sample_tools:
        tool_text = f"{tool.name} {tool.description} {' '.join(tool.keywords)}"
        tool.combined_embedding = embedding_model.get_embedding(tool_text)
        tools_with_embeddings.append(tool)
    
    # Test with weather query
    weather_query = "What's the temperature outside?"
    result = selector.select_tool(weather_query, tools_with_embeddings)
    assert len(result) > 0  # Should have at least one result
    assert result[0][0].name == "weather_lookup"  # First result should be weather tool
    
    # Test with math query
    math_query = "Help me with arithmetic"
    result = selector.select_tool(math_query, tools_with_embeddings)
    assert len(result) > 0
    assert result[0][0].name == "calculator"
    
    # Test hybrid strategy
    hybrid_selector = ToolSelector(selection_strategy="hybrid", embedding_model=embedding_model)
    result = hybrid_selector.select_tool(math_query, tools_with_embeddings)
    assert len(result) > 0
    assert result[0][0].name == "calculator"

@pytest.mark.asyncio
async def test_registry_integration(registry_client, embedding_model):
    """Test integration with registry client."""
    selector = ToolSelector.create_with_registry_client(
        registry_client=registry_client,
        selection_strategy="keyword_match",
        embedding_model=embedding_model
    )
    
    # Test selecting from registry
    result = await selector.select_from_registry(
        query="weather forecast",
        query_registry=True,
        registry_query_params={"categories": ["weather"]},
        threshold=0.1
    )
    
    assert len(result) > 0
    assert result[0][0].name == "weather_lookup"
    
    # Test with local tools and registry
    local_tools = [
        ToolDescription(
            name="local_tool",
            description="A locally available tool",
            categories=["local"],
            keywords=["local", "tool"]
        )
    ]
    
    result = await selector.select_from_registry(
        query="local tool",
        query_registry=True,
        local_tools=local_tools
    )
    
    assert len(result) > 0
    assert result[0][0].name == "local_tool"  # Local tool should match best

"""Integration tests for the A2A protocol registry integration.

This module tests the integration with A2A registry services for agent discovery.
"""
import asyncio
import logging
import unittest
from typing import Dict, List, Optional

import pytest
import requests

from ailf.communication.a2a_client import A2AClient
from ailf.communication.a2a_registry import (
    A2ARegistry,
    A2ARegistryClient,
    A2ARegistryError,
    RegistryEntry,
)
from ailf.schemas.a2a import AgentCard


class TestA2ARegistryClient(unittest.TestCase):
    """Test the A2A registry client."""
    
    @pytest.mark.asyncio
    async def test_registry_connection(self):
        """Test connecting to a registry."""
        # Create a client with a mock registry URL
        registry_client = A2ARegistryClient(base_url="https://example.com/registry")
        
        # Mock the registry response
        registry_client._request = unittest.mock.AsyncMock(return_value={
            "status": "success",
            "agents": [
                {
                    "id": "agent-1",
                    "name": "Test Agent 1",
                    "description": "A test agent",
                    "url": "https://example.com/agent1",
                    "provider": {"name": "Test Provider", "url": "https://example.com"}
                },
                {
                    "id": "agent-2",
                    "name": "Test Agent 2",
                    "description": "Another test agent",
                    "url": "https://example.com/agent2",
                    "provider": {"name": "Test Provider", "url": "https://example.com"}
                }
            ]
        })
        
        # Test listing agents
        agents = await registry_client.list_agents()
        assert len(agents) == 2
        assert agents[0].id == "agent-1"
        assert agents[0].name == "Test Agent 1"
        assert agents[1].id == "agent-2"
        
        # Test getting a specific agent
        registry_client._request = unittest.mock.AsyncMock(return_value={
            "agent": {
                "id": "agent-1",
                "name": "Test Agent 1",
                "description": "A test agent",
                "url": "https://example.com/agent1",
                "provider": {"name": "Test Provider", "url": "https://example.com"}
            }
        })
        
        agent = await registry_client.get_agent("agent-1")
        assert agent.id == "agent-1"
        assert agent.name == "Test Agent 1"
    
    @pytest.mark.asyncio
    async def test_agent_registration(self):
        """Test registering an agent with the registry."""
        # Create a client with a mock registry URL
        registry_client = A2ARegistryClient(base_url="https://example.com/registry")
        
        # Create a mock agent card
        agent_card = AgentCard(
            name="Test Agent",
            description="A test agent for registration",
            url="https://example.com/my-agent",
            provider={"name": "Test Provider", "url": "https://example.com"},
            version="1.0.0",
            capabilities={"streaming": True}
        )
        
        # Mock the registration response
        registry_client._request = unittest.mock.AsyncMock(return_value={
            "status": "success",
            "agent_id": "new-agent-123",
            "message": "Agent registered successfully"
        })
        
        # Test registering the agent
        result = await registry_client.register_agent(agent_card)
        assert result.get("status") == "success"
        assert result.get("agent_id") == "new-agent-123"
        
        # Test updating the agent
        registry_client._request = unittest.mock.AsyncMock(return_value={
            "status": "success",
            "message": "Agent updated successfully"
        })
        
        updated_agent = agent_card.model_copy(update={"description": "Updated description"})
        result = await registry_client.update_agent("new-agent-123", updated_agent)
        assert result.get("status") == "success"
        
        # Test deregistering the agent
        registry_client._request = unittest.mock.AsyncMock(return_value={
            "status": "success",
            "message": "Agent deregistered successfully"
        })
        
        result = await registry_client.deregister_agent("new-agent-123")
        assert result.get("status") == "success"
    
    @pytest.mark.asyncio
    async def test_agent_search(self):
        """Test searching for agents in the registry."""
        # Create a client with a mock registry URL
        registry_client = A2ARegistryClient(base_url="https://example.com/registry")
        
        # Mock the search response
        registry_client._request = unittest.mock.AsyncMock(return_value={
            "status": "success",
            "results": [
                {
                    "id": "agent-1",
                    "name": "Search Agent 1",
                    "description": "An agent that matches the search query",
                    "url": "https://example.com/agent1",
                    "provider": {"name": "Test Provider", "url": "https://example.com"},
                    "score": 0.95
                },
                {
                    "id": "agent-3",
                    "name": "Search Agent 3",
                    "description": "Another agent that matches the search query",
                    "url": "https://example.com/agent3",
                    "provider": {"name": "Test Provider", "url": "https://example.com"},
                    "score": 0.82
                }
            ]
        })
        
        # Test searching agents by query
        search_results = await registry_client.search_agents("search query")
        assert len(search_results) == 2
        assert search_results[0].id == "agent-1"
        assert search_results[0].name == "Search Agent 1"
        assert search_results[0].score == 0.95
        assert search_results[1].id == "agent-3"
        assert search_results[1].score == 0.82
        
        # Test searching agents by capability
        registry_client._request = unittest.mock.AsyncMock(return_value={
            "status": "success",
            "results": [
                {
                    "id": "agent-2",
                    "name": "Streaming Agent",
                    "description": "An agent that supports streaming",
                    "url": "https://example.com/agent2",
                    "provider": {"name": "Test Provider", "url": "https://example.com"},
                    "capabilities": {"streaming": True}
                }
            ]
        })
        
        capability_results = await registry_client.search_agents_by_capability({"streaming": True})
        assert len(capability_results) == 1
        assert capability_results[0].id == "agent-2"
        assert capability_results[0].name == "Streaming Agent"
        assert capability_results[0].capabilities.get("streaming") == True


class TestA2ARegistry(unittest.TestCase):
    """Test the local A2A registry."""
    
    def test_local_registry(self):
        """Test local registry operations."""
        registry = A2ARegistry()
        
        # Add some agents
        agent1 = RegistryEntry(
            id="local-agent-1",
            name="Local Agent 1",
            description="A locally registered agent",
            url="https://localhost:8000",
            provider={"name": "Local Provider", "url": "https://localhost"}
        )
        
        agent2 = RegistryEntry(
            id="local-agent-2",
            name="Local Agent 2",
            description="Another locally registered agent",
            url="https://localhost:8001",
            provider={"name": "Local Provider", "url": "https://localhost"}
        )
        
        registry.register_agent(agent1)
        registry.register_agent(agent2)
        
        # Test retrieving agents
        agents = registry.list_agents()
        assert len(agents) == 2
        
        # Test getting a specific agent
        retrieved_agent = registry.get_agent("local-agent-1")
        assert retrieved_agent is not None
        assert retrieved_agent.id == "local-agent-1"
        assert retrieved_agent.name == "Local Agent 1"
        
        # Test updating an agent
        updated_agent = agent1.model_copy(update={"description": "Updated local agent"})
        registry.update_agent("local-agent-1", updated_agent)
        
        # Verify the update
        retrieved_updated = registry.get_agent("local-agent-1")
        assert retrieved_updated.description == "Updated local agent"
        
        # Test deregistering an agent
        registry.deregister_agent("local-agent-2")
        remaining_agents = registry.list_agents()
        assert len(remaining_agents) == 1
        assert remaining_agents[0].id == "local-agent-1"


if __name__ == "__main__":
    unittest.main()

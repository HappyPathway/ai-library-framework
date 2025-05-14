"""A2A registry integration for AILF.

This module provides client and server implementations for A2A agent registry services,
allowing for agent discovery and registration.
"""
import json
import logging
import os
from datetime import datetime, UTC
from typing import Dict, List, Optional, Union, Any

import httpx
from pydantic import BaseModel, Field

from ailf.schemas.a2a import AgentCard

logger = logging.getLogger(__name__)


class RegistryEntry(BaseModel):
    """Registry entry for an A2A agent."""
    id: str
    name: str
    description: str
    url: str
    provider: Dict[str, str]
    capabilities: Optional[Dict[str, bool]] = None
    skills: Optional[List[Dict[str, Any]]] = None
    version: Optional[str] = None
    documentationUrl: Optional[str] = None
    avatar: Optional[str] = None
    authentication: Optional[Dict[str, Any]] = None
    score: Optional[float] = None
    registered_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


class A2ARegistryError(Exception):
    """Base exception for A2A registry errors."""
    pass


class A2ARegistryConnectionError(A2ARegistryError):
    """Exception raised when a connection to the registry fails."""
    def __init__(self, message: str, original_error: Optional[Exception] = None):
        self.original_error = original_error
        super().__init__(f"Registry connection error: {message}")


class A2ARegistryClientError(A2ARegistryError):
    """Exception raised when a registry client operation fails."""
    pass


class A2ARegistry:
    """Simple in-memory A2A agent registry implementation."""
    
    def __init__(self):
        """Initialize an empty registry."""
        self.agents: Dict[str, RegistryEntry] = {}
    
    def register_agent(self, agent: RegistryEntry) -> None:
        """Register an agent in the registry.
        
        Args:
            agent: The agent to register.
        """
        agent_copy = agent.model_copy()
        if not agent_copy.registered_at:
            agent_copy.registered_at = datetime.now(UTC)
        agent_copy.updated_at = datetime.now(UTC)
        self.agents[agent_copy.id] = agent_copy
    
    def update_agent(self, agent_id: str, agent: RegistryEntry) -> None:
        """Update an existing agent in the registry.
        
        Args:
            agent_id: The ID of the agent to update.
            agent: The updated agent data.
            
        Raises:
            A2ARegistryError: If the agent does not exist.
        """
        if agent_id not in self.agents:
            raise A2ARegistryError(f"Agent {agent_id} not found in registry")
        
        agent_copy = agent.model_copy()
        agent_copy.updated_at = datetime.now(UTC)
        
        # Preserve registration time if it exists
        if self.agents[agent_id].registered_at:
            agent_copy.registered_at = self.agents[agent_id].registered_at
            
        self.agents[agent_id] = agent_copy
    
    def deregister_agent(self, agent_id: str) -> None:
        """Remove an agent from the registry.
        
        Args:
            agent_id: The ID of the agent to remove.
            
        Raises:
            A2ARegistryError: If the agent does not exist.
        """
        if agent_id not in self.agents:
            raise A2ARegistryError(f"Agent {agent_id} not found in registry")
        
        del self.agents[agent_id]
    
    def get_agent(self, agent_id: str) -> Optional[RegistryEntry]:
        """Get an agent by ID.
        
        Args:
            agent_id: The ID of the agent to get.
            
        Returns:
            The agent, or None if not found.
        """
        return self.agents.get(agent_id)
    
    def list_agents(self) -> List[RegistryEntry]:
        """List all agents in the registry.
        
        Returns:
            A list of all registered agents.
        """
        return list(self.agents.values())


class A2ARegistryClient:
    """Client for interacting with an A2A registry service."""
    
    def __init__(self, base_url: str):
        """Initialize a registry client.
        
        Args:
            base_url: The base URL of the registry service.
        """
        self.base_url = base_url
        
    async def _request(self, method: str, path: str, **kwargs) -> Dict[str, Any]:
        """Make an HTTP request to the registry.
        
        Args:
            method: The HTTP method to use.
            path: The path to request.
            **kwargs: Additional arguments to pass to httpx.
            
        Returns:
            The JSON response from the registry.
            
        Raises:
            A2ARegistryConnectionError: If the connection fails.
            A2ARegistryClientError: If the request fails.
        """
        url = f"{self.base_url}/{path.lstrip('/')}"
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.request(method, url, **kwargs)
                response.raise_for_status()
                return response.json()
        except httpx.HTTPStatusError as e:
            error_detail = f"HTTP {e.response.status_code}"
            try:
                error_data = e.response.json()
                if "message" in error_data:
                    error_detail += f": {error_data['message']}"
                elif "error" in error_data:
                    error_detail += f": {error_data['error']}"
            except Exception:
                if e.response.text:
                    error_detail += f": {e.response.text[:100]}"
            
            raise A2ARegistryClientError(error_detail)
        except httpx.RequestError as e:
            raise A2ARegistryConnectionError(str(e), e)
        except Exception as e:
            raise A2ARegistryError(f"Unexpected error: {str(e)}")
    
    async def list_agents(self) -> List[RegistryEntry]:
        """List all agents in the registry.
        
        Returns:
            A list of all registered agents.
            
        Raises:
            A2ARegistryConnectionError: If the connection fails.
            A2ARegistryClientError: If the request fails.
        """
        response = await self._request("GET", "/agents")
        
        if "agents" not in response:
            raise A2ARegistryClientError("Invalid response from registry: missing 'agents' field")
        
        return [RegistryEntry(**agent) for agent in response["agents"]]
    
    async def get_agent(self, agent_id: str) -> RegistryEntry:
        """Get an agent by ID.
        
        Args:
            agent_id: The ID of the agent to get.
            
        Returns:
            The agent.
            
        Raises:
            A2ARegistryConnectionError: If the connection fails.
            A2ARegistryClientError: If the request fails or the agent is not found.
        """
        response = await self._request("GET", f"/agents/{agent_id}")
        
        if "agent" not in response:
            raise A2ARegistryClientError("Invalid response from registry: missing 'agent' field")
        
        return RegistryEntry(**response["agent"])
    
    async def search_agents(self, query: str) -> List[RegistryEntry]:
        """Search for agents by query string.
        
        Args:
            query: The search query.
            
        Returns:
            A list of matching agents.
            
        Raises:
            A2ARegistryConnectionError: If the connection fails.
            A2ARegistryClientError: If the request fails.
        """
        response = await self._request("GET", "/agents/search", params={"q": query})
        
        if "results" not in response:
            raise A2ARegistryClientError("Invalid response from registry: missing 'results' field")
        
        return [RegistryEntry(**agent) for agent in response["results"]]
    
    async def search_agents_by_capability(self, capabilities: Dict[str, bool]) -> List[RegistryEntry]:
        """Search for agents by capabilities.
        
        Args:
            capabilities: The capabilities to search for.
            
        Returns:
            A list of matching agents.
            
        Raises:
            A2ARegistryConnectionError: If the connection fails.
            A2ARegistryClientError: If the request fails.
        """
        response = await self._request(
            "GET", 
            "/agents/search",
            params={"capabilities": json.dumps(capabilities)}
        )
        
        if "results" not in response:
            raise A2ARegistryClientError("Invalid response from registry: missing 'results' field")
        
        return [RegistryEntry(**agent) for agent in response["results"]]
    
    async def register_agent(self, agent_card: AgentCard) -> Dict[str, Any]:
        """Register an agent with the registry.
        
        Args:
            agent_card: The agent card to register.
            
        Returns:
            The response from the registry.
            
        Raises:
            A2ARegistryConnectionError: If the connection fails.
            A2ARegistryClientError: If the request fails.
        """
        agent_data = agent_card.model_dump(exclude_none=True)
        return await self._request("POST", "/agents", json=agent_data)
    
    async def update_agent(self, agent_id: str, agent_card: AgentCard) -> Dict[str, Any]:
        """Update an existing agent in the registry.
        
        Args:
            agent_id: The ID of the agent to update.
            agent_card: The updated agent card.
            
        Returns:
            The response from the registry.
            
        Raises:
            A2ARegistryConnectionError: If the connection fails.
            A2ARegistryClientError: If the request fails.
        """
        agent_data = agent_card.model_dump(exclude_none=True)
        return await self._request("PUT", f"/agents/{agent_id}", json=agent_data)
    
    async def deregister_agent(self, agent_id: str) -> Dict[str, Any]:
        """Remove an agent from the registry.
        
        Args:
            agent_id: The ID of the agent to remove.
            
        Returns:
            The response from the registry.
            
        Raises:
            A2ARegistryConnectionError: If the connection fails.
            A2ARegistryClientError: If the request fails.
        """
        return await self._request("DELETE", f"/agents/{agent_id}")


class A2ARegistryManager:
    """Manager for discovering and interacting with A2A agents."""
    
    def __init__(self, registry_url: Optional[str] = None):
        """Initialize the registry manager.
        
        Args:
            registry_url: URL of the remote registry service. If None, uses local registry.
        """
        self.local_registry = A2ARegistry()
        self.remote_client = A2ARegistryClient(registry_url) if registry_url else None
        
    async def discover_agent(self, agent_id: str) -> Optional[RegistryEntry]:
        """Discover an agent by ID from local or remote registry.
        
        Args:
            agent_id: The ID of the agent to discover.
            
        Returns:
            The discovered agent, or None if not found.
        """
        # First check local registry
        agent = self.local_registry.get_agent(agent_id)
        if agent:
            return agent
            
        # Then check remote registry if available
        if self.remote_client:
            try:
                return await self.remote_client.get_agent(agent_id)
            except A2ARegistryError:
                logger.warning(f"Error getting agent {agent_id} from remote registry", exc_info=True)
                
        return None
        
    async def search_agents(self, query: str) -> List[RegistryEntry]:
        """Search for agents by query string.
        
        Args:
            query: The search query.
            
        Returns:
            A list of matching agents from both local and remote registries.
        """
        results = []
        
        # Search local registry (simple string matching)
        for agent in self.local_registry.list_agents():
            if (query.lower() in agent.name.lower() or 
                query.lower() in agent.description.lower()):
                results.append(agent)
                
        # Search remote registry if available
        if self.remote_client:
            try:
                remote_results = await self.remote_client.search_agents(query)
                
                # Combine results, avoiding duplicates by ID
                local_ids = {r.id for r in results}
                for remote_agent in remote_results:
                    if remote_agent.id not in local_ids:
                        results.append(remote_agent)
                        
            except A2ARegistryError:
                logger.warning(f"Error searching agents with query '{query}' in remote registry", 
                               exc_info=True)
                
        return results
        
    async def get_client_for_agent(self, agent_id: str) -> Optional["A2AClient"]:
        """Get an A2A client for a specific agent.
        
        Args:
            agent_id: The ID of the agent to get a client for.
            
        Returns:
            An A2AClient configured for the agent, or None if agent not found.
        """
        # Local import to avoid circular dependency
        from ailf.communication.a2a_client import A2AClient
        
        agent = await self.discover_agent(agent_id)
        if not agent:
            return None
            
        return A2AClient(base_url=agent.url)

"""Pydantic schemas for agent descriptions and registry interactions."""
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field
import uuid
from datetime import datetime

from ailf.schemas.a2a import AgentCard, AgentProvider, AgentCapabilities, AgentAuthentication

class CommunicationEndpoint(BaseModel):
    """Describes a communication endpoint for an agent."""
    protocol: str = Field(..., description="Communication protocol (e.g., 'http', 'redis_streams', 'zmq').")
    address: str = Field(..., description="The address or identifier for the endpoint (e.g., URL, topic name, connection string).")
    details: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Additional protocol-specific details.")

class CapabilityDetail(BaseModel):
    """Describes a specific capability of an agent in more detail."""
    name: str = Field(..., description="Name of the capability (e.g., 'summarize_text', 'execute_python_code').")
    description: str = Field(..., description="Detailed description of what the capability does.")
    input_schema_ref: Optional[str] = Field(default=None, description="Reference to Pydantic model for input (e.g., 'module.ClassName').")
    output_schema_ref: Optional[str] = Field(default=None, description="Reference to Pydantic model for output (e.g., 'module.ClassName').")
    metadata: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Additional metadata about the capability.")

class AgentDescription(BaseModel):
    """Comprehensive description of an AI agent for discovery and interaction."""
    agent_id: str = Field(default_factory=lambda: str(uuid.uuid4()), description="Unique identifier for the agent.")
    agent_name: str = Field(..., description="Human-readable name for the agent.")
    agent_type: str = Field(..., description="Type or role of the agent (e.g., 'general_assistant', 'code_generator', 'data_analyst').")
    description: str = Field(..., description="Detailed description of the agent's purpose and functionality.")
    
    version: str = Field(default="1.0.0", description="Version of the agent implementation.")
    author: Optional[str] = Field(default=None, description="Author or maintainer of the agent.")
    
    capabilities: List[CapabilityDetail] = Field(default_factory=list, description="List of detailed capabilities offered by the agent.")
    supported_acp_versions: List[str] = Field(default_factory=lambda: ["1.0"], description="List of Agent Communication Protocol versions supported.")
    communication_endpoints: List[CommunicationEndpoint] = Field(default_factory=list, description="List of communication endpoints where the agent can be reached.")
    
    tool_references: List[str] = Field(default_factory=list, description="Names or IDs of tools this agent primarily uses or exposes.")
    dependencies: List[str] = Field(default_factory=list, description="List of other agent IDs or service names this agent depends on.")
    
    status: Optional[str] = Field(default=None, description="Current operational status (e.g., 'online', 'offline', 'busy'). This is often dynamic and might be part of live status updates rather than static description.")
    last_seen: Optional[datetime] = Field(default=None, description="Timestamp of when the agent was last active or registered.")

    # Metadata for advanced features as per roadmap
    ontologies_used: List[str] = Field(default_factory=list, description="List of ontologies or knowledge domains the agent specializes in.")
    historical_performance_metrics: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Aggregated historical performance data.")
    cost_information: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Information related to the cost of using this agent.")
    embedding: Optional[List[float]] = Field(default=None, description="Embedding of the agent's description for semantic search in a registry.")
    
    # A2A protocol support
    supports_a2a: bool = Field(default=False, description="Whether this agent supports the A2A protocol.")
    a2a_capabilities: Optional[AgentCapabilities] = Field(default=None, description="Agent capabilities for A2A protocol.")
    
    metadata: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Additional custom metadata for the agent.")

    class Config:
        validate_assignment = True
        
    def to_a2a_agent_card(self) -> AgentCard:
        """Convert AgentDescription to A2A-compatible AgentCard.
        
        Returns:
            AgentCard: A2A-compatible agent card representation.
        
        Example:
            >>> agent_desc = AgentDescription(agent_name="MyAgent", agent_type="assistant", description="A helpful agent")
            >>> agent_card = agent_desc.to_a2a_agent_card()
        """
        # Create provider information
        provider = AgentProvider(
            name=self.author or "Unknown",
            url=next((e.address for e in self.communication_endpoints 
                    if e.protocol == "http" or e.protocol == "https"), None)
        )
        
        # Get HTTP endpoint for the agent
        agent_url = next((e.address for e in self.communication_endpoints 
                        if e.protocol == "http" or e.protocol == "https"), "")
                        
        # Create authentication if needed
        authentication = None
        for endpoint in self.communication_endpoints:
            if endpoint.details and endpoint.details.get("authentication"):
                auth_details = endpoint.details.get("authentication", {})
                authentication = AgentAuthentication(
                    schemes=auth_details.get("schemes", ["none"]),
                    credentials=auth_details.get("credentials")
                )
                break
                
        # Create the AgentCard
        return AgentCard(
            name=self.agent_name,
            description=self.description,
            url=agent_url,
            provider=provider,
            version=self.version,
            documentationUrl=self.metadata.get("documentation_url"),
            capabilities=self.a2a_capabilities or AgentCapabilities(),
            authentication=authentication,
            metadata=self.metadata
        )

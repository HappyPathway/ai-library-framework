import pytest
from ailf.schemas.mcp import MCPMessage

def test_mcp_message_schema():
    """Test the MCPMessage schema for correct initialization."""
    message = MCPMessage(
        message_id="12345",
        capabilities=["contextual_data_injection", "function_routing"],
        payload={"key": "value"}
    )

    assert message.protocol == "MCP"
    assert message.version == "1.0.0"
    assert message.message_id == "12345"
    assert "contextual_data_injection" in message.capabilities
    assert message.payload["key"] == "value"

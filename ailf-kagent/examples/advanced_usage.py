"""
Advanced integration example demonstrating the full AILF-Kagent integration.

This example showcases more advanced features of the integration, including:
- AILF ReAct reasoning with Kagent agents
- Memory sharing between frameworks
- Using multiple AILF tools with Kagent
"""

import asyncio
from typing import Dict, List, Any, Optional
from pydantic import BaseModel, Field

# Import Kagent components
from kagent.agents import Agent as KAgent
from kagent.schema import AgentResponse

# Import AILF components
from ailf.tooling import ToolDescription, ToolManager
from ailf.memory import MemoryManager as AILFMemory

# Import the integration adapters
from ailf_kagent.adapters.tools import AILFToolAdapter
from ailf_kagent.adapters.agents import AILFEnabledAgent, ReActAgent
from ailf_kagent.adapters.memory import AILFMemoryBridge, SharedMemoryManager


# Define a few AILF tools using Pydantic models
class WeatherInput(BaseModel):
    """Input for the weather tool"""
    location: str = Field(..., description="City or location to get weather for")
    units: str = Field(default="celsius", description="Temperature units (celsius or fahrenheit)")


class WeatherOutput(BaseModel):
    """Output from the weather tool"""
    temperature: float = Field(..., description="Current temperature")
    condition: str = Field(..., description="Weather condition (sunny, cloudy, etc.)")
    humidity: Optional[int] = Field(None, description="Humidity percentage")
    location: str = Field(..., description="Location for which weather is reported")


async def weather_tool(input_data: WeatherInput) -> WeatherOutput:
    """Get weather information for a location (simulated)"""
    # This is a simulated tool - in a real implementation, it would call a weather API
    location = input_data.location.lower()
    
    # Simulated weather data
    weather_data = {
        "new york": {"temp": 22, "condition": "partly cloudy", "humidity": 65},
        "london": {"temp": 18, "condition": "rainy", "humidity": 80},
        "tokyo": {"temp": 26, "condition": "sunny", "humidity": 70},
        "sydney": {"temp": 24, "condition": "clear", "humidity": 60},
        # Default for unknown locations
        "default": {"temp": 20, "condition": "unknown", "humidity": 50}
    }
    
    # Get weather for the location or use default
    data = weather_data.get(location, weather_data["default"])
    
    # Convert temperature if needed
    temp = data["temp"]
    if input_data.units.lower() == "fahrenheit":
        temp = (temp * 9/5) + 32
    
    return WeatherOutput(
        temperature=temp,
        condition=data["condition"],
        humidity=data["humidity"],
        location=input_data.location
    )


class NoteInput(BaseModel):
    """Input for the note-taking tool"""
    action: str = Field(..., description="Action to perform: 'add', 'get', or 'list'")
    title: Optional[str] = Field(None, description="Title of the note (for add/get)")
    content: Optional[str] = Field(None, description="Content of the note (for add)")


class NoteOutput(BaseModel):
    """Output from the note-taking tool"""
    success: bool = Field(..., description="Whether the operation was successful")
    message: str = Field(..., description="Status message")
    notes: Optional[Dict[str, str]] = Field(None, description="Notes (for list/get actions)")


class NoteTool:
    """Tool for taking and retrieving notes with memory integration"""
    
    def __init__(self, memory_manager: SharedMemoryManager):
        """Initialize the note tool with a memory manager
        
        Args:
            memory_manager: The shared memory manager for storing notes
        """
        self.memory = memory_manager
        self.notes_key = "user_notes"
    
    async def _get_notes(self) -> Dict[str, str]:
        """Get all stored notes
        
        Returns:
            Dictionary of note titles to content
        """
        notes = await self.memory.kagent_memory.get(self.notes_key)
        if not notes:
            return {}
        return notes
    
    async def _save_notes(self, notes: Dict[str, str]) -> None:
        """Save the notes dictionary
        
        Args:
            notes: Dictionary of notes to save
        """
        await self.memory.kagent_memory.set(self.notes_key, notes)
    
    async def execute(self, input_data: NoteInput) -> NoteOutput:
        """Execute the note-taking tool
        
        Args:
            input_data: The input parameters for the note operation
            
        Returns:
            The result of the note operation
        """
        action = input_data.action.lower()
        notes = await self._get_notes()
        
        if action == "add":
            if not input_data.title or not input_data.content:
                return NoteOutput(
                    success=False,
                    message="Title and content are required for adding notes"
                )
            
            notes[input_data.title] = input_data.content
            await self._save_notes(notes)
            return NoteOutput(
                success=True,
                message=f"Note '{input_data.title}' added successfully"
            )
            
        elif action == "get":
            if not input_data.title:
                return NoteOutput(
                    success=False,
                    message="Title is required for getting notes"
                )
            
            content = notes.get(input_data.title)
            if content:
                return NoteOutput(
                    success=True,
                    message=f"Retrieved note '{input_data.title}'",
                    notes={input_data.title: content}
                )
            else:
                return NoteOutput(
                    success=False,
                    message=f"Note '{input_data.title}' not found"
                )
                
        elif action == "list":
            return NoteOutput(
                success=True,
                message=f"Found {len(notes)} notes",
                notes=notes
            )
            
        else:
            return NoteOutput(
                success=False,
                message=f"Unknown action: {action}"
            )


async def main():
    """Run the advanced integration example"""
    print("Starting AILF-Kagent Advanced Integration Example")
    
    # Create a shared memory manager for both frameworks
    memory_manager = SharedMemoryManager(namespace="advanced_example")
    
    # Create note-taking tool that uses shared memory
    note_tool_instance = NoteTool(memory_manager)
    
    # Create AILF tool descriptions
    weather_tool_desc = ToolDescription(
        id="weather",
        name="Weather Info",
        description="Get current weather information for a location",
        function=weather_tool,
        input_schema=WeatherInput,
        output_schema=WeatherOutput
    )
    
    note_tool_desc = ToolDescription(
        id="notes",
        name="Note Taking",
        description="Take and retrieve notes",
        function=note_tool_instance.execute,
        input_schema=NoteInput,
        output_schema=NoteOutput
    )
    
    # Create AILF-to-Kagent tool adapters
    weather_adapter = AILFToolAdapter(weather_tool_desc)
    note_adapter = AILFToolAdapter(note_tool_desc)
    
    # Create a ReAct-enhanced Kagent agent with the adapted tools
    # This agent will use AILF's ReAct processor for reasoning
    agent = ReActAgent(
        tools=[weather_adapter, note_adapter],
    )
    
    # Test taking notes
    print("\n=== Testing Note Taking ===")
    user_query = "Take a note with title 'Meeting' and content 'Discuss project timeline with team'"
    print(f"\nUser query: {user_query}")
    
    response = await agent.run(user_query)
    print("\nAgent response:")
    print(response.messages[0].content)
    
    # Test weather information
    print("\n=== Testing Weather Information ===")
    user_query = "What's the weather like in Tokyo and London?"
    print(f"\nUser query: {user_query}")
    
    response = await agent.run(user_query)
    print("\nAgent response:")
    print(response.messages[0].content)
    
    # Test retrieving notes
    print("\n=== Testing Note Retrieval ===")
    user_query = "What notes do I have?"
    print(f"\nUser query: {user_query}")
    
    response = await agent.run(user_query)
    print("\nAgent response:")
    print(response.messages[0].content)
    
    # Test a complex multi-step query requiring reasoning
    print("\n=== Testing Complex Reasoning ===")
    user_query = """
    I need to plan a meeting. First, check the weather in London for reference.
    Then create a note with the title 'London Meeting' and content that includes
    the current temperature and a reminder to bring an umbrella if it's rainy.
    """
    print(f"\nUser query: {user_query}")
    
    response = await agent.run(user_query)
    print("\nAgent response:")
    print(response.messages[0].content)
    
    # Check if the reasoning steps are included in metadata
    if response.metadata and "reasoning_trace" in response.metadata:
        print("\nReasoning steps:")
        for i, step in enumerate(response.metadata["reasoning_trace"]):
            print(f"Step {i+1}: {step.get('thought', '')}")
    
    # Retrieve the final note to verify
    print("\n=== Verifying Final Note ===")
    user_query = "Show me the 'London Meeting' note"
    print(f"\nUser query: {user_query}")
    
    response = await agent.run(user_query)
    print("\nAgent response:")
    print(response.messages[0].content)
    
    print("\nExample completed successfully")


if __name__ == "__main__":
    asyncio.run(main())

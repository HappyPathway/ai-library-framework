"""
Example demonstrating how to use AILF tools with Kagent teams.

This example shows:
1. Creating a team of Kagent agents with specialized roles
2. Enhancing the team with AILF cognitive capabilities
3. Using AILF tools across multiple agents
4. Sharing memory between team members
"""

import asyncio
from typing import Dict, List, Optional, Any
from pydantic import BaseModel, Field

# Import AILF components
from ailf.tooling import ToolDescription, ToolManager
from ailf.schemas import BaseSchema

# Import Kagent components
from kagent.agents import Agent as KAgent
from kagent.agents.team import Team
from kagent.schema import AgentResponse

# Import the integration adapters
from ailf_kagent.adapters.tools import AILFToolAdapter, AILFToolRegistry
from ailf_kagent.adapters.agents import AILFEnabledAgent, ReActAgent
from ailf_kagent.adapters.memory import SharedMemoryManager


#
# Define AILF research and analysis tools
#

class WebSearchInput(BaseModel):
    """Input for web search tool"""
    query: str = Field(..., description="Search query")
    num_results: int = Field(5, description="Number of results to return", ge=1, le=10)


class SearchResult(BaseModel):
    """A single search result"""
    title: str = Field(..., description="Title of the result")
    url: str = Field(..., description="URL of the result")
    snippet: str = Field(..., description="Snippet or summary of the result")


class WebSearchOutput(BaseModel):
    """Output from web search tool"""
    results: List[SearchResult] = Field(..., description="Search results")
    total_found: int = Field(..., description="Total number of results found")


class FactCheckInput(BaseModel):
    """Input for fact checking tool"""
    statement: str = Field(..., description="Statement to fact check")
    sources: Optional[List[str]] = Field(None, description="Sources to check against")


class FactCheckOutput(BaseModel):
    """Output from fact checking tool"""
    verified: bool = Field(..., description="Whether the statement is verified")
    confidence: float = Field(..., description="Confidence score (0-1)", ge=0, le=1)
    evidence: List[str] = Field(..., description="Evidence supporting the verification")
    contradictions: List[str] = Field(default_factory=list, description="Contradicting evidence if any")


# Mock data for the example
SEARCH_RESULTS = {
    "climate change": [
        SearchResult(
            title="Climate Change: Evidence and Causes", 
            url="https://climate.nasa.gov/evidence/", 
            snippet="The Earth's climate has changed throughout history. Just in the last 800,000 years..."
        ),
        SearchResult(
            title="Global Warming and Climate Change - United Nations", 
            url="https://www.un.org/en/climatechange", 
            snippet="Climate Change is the defining issue of our time and we are at a defining moment..."
        ),
        SearchResult(
            title="What is Climate Change? | Definition, Causes and Effects", 
            url="https://www.nationalgeographic.com/environment/article/global-warming-overview", 
            snippet="Climate change is the long-term alteration in Earth's climate and weather patterns..."
        ),
    ],
    "renewable energy": [
        SearchResult(
            title="Renewable Energy Explained - Types, Forms & Sources", 
            url="https://www.epa.gov/renewable-energy", 
            snippet="Renewable energy is energy from sources that are naturally replenishing but flow-limited..."
        ),
        SearchResult(
            title="Renewable Energy | Department of Energy", 
            url="https://www.energy.gov/renewable-energy", 
            snippet="Renewable energy technologies turn these natural resources into usable forms of energy..."
        ),
    ]
}

FACT_CHECK_DATA = {
    "The Earth is flat": {
        "verified": False,
        "confidence": 1.0,
        "evidence": [
            "Satellite imagery shows Earth as a sphere",
            "Ships disappear hull-first over the horizon",
            "Earth casts a round shadow on the Moon during lunar eclipses"
        ],
        "contradictions": []
    },
    "Climate change is real": {
        "verified": True,
        "confidence": 0.98,
        "evidence": [
            "Global temperature rise of 1.8°F since 1901",
            "Declining Arctic sea ice",
            "Sea level rise of 8 inches in the last century",
            "Increasing extreme weather events"
        ],
        "contradictions": []
    }
}


async def web_search(input_data: WebSearchInput) -> WebSearchOutput:
    """Perform a web search.
    
    In a real implementation, this would connect to a search API.
    """
    query = input_data.query.lower()
    
    # Find matching results
    results = []
    for key, items in SEARCH_RESULTS.items():
        if key in query:
            results.extend(items[:input_data.num_results])
    
    # If no specific matches, return generic results
    if not results:
        # Just return a sample for this example
        sample_key = list(SEARCH_RESULTS.keys())[0]
        results = SEARCH_RESULTS[sample_key][:input_data.num_results]
    
    return WebSearchOutput(
        results=results,
        total_found=len(results)
    )


async def fact_check(input_data: FactCheckInput) -> FactCheckOutput:
    """Check facts against known information.
    
    In a real implementation, this would use an LLM or fact-checking API.
    """
    statement = input_data.statement.lower()
    
    # Check if we have direct matches
    for key, data in FACT_CHECK_DATA.items():
        if key.lower() in statement:
            return FactCheckOutput(**data)
    
    # For this example, default to uncertain if no match
    return FactCheckOutput(
        verified=False,
        confidence=0.5,
        evidence=["No direct evidence found for this statement"],
        contradictions=[]
    )


async def create_research_team():
    """Create a research team of specialized agents."""
    # Create shared memory for the team
    shared_memory = SharedMemoryManager(namespace="research_team")
    
    # Create AILF tools
    search_tool = ToolDescription(
        id="web-search",
        description="Search the web for information",
        input_schema=WebSearchInput,
        output_schema=WebSearchOutput,
        function=web_search
    )
    
    fact_check_tool = ToolDescription(
        id="fact-check",
        description="Verify if a statement is factual",
        input_schema=FactCheckInput,
        output_schema=FactCheckOutput,
        function=fact_check
    )
    
    # Create tool registry
    registry = AILFToolRegistry()
    registry.register(search_tool)
    registry.register(fact_check_tool)
    
    # Create specialized agents
    
    # Research agent - uses ReAct for detailed analysis
    researcher = ReActAgent(
        name="Researcher",
        memory=shared_memory.kagent_memory,
        description="Specialized in gathering and analyzing information"
    )
    # Add search tool to researcher
    researcher.add_tool(AILFToolAdapter(search_tool))
    
    # Fact checker - uses ReAct for verification
    fact_checker = ReActAgent(
        name="FactChecker",
        memory=shared_memory.kagent_memory,
        description="Specialized in verifying information accuracy"
    )
    # Add fact check tool to fact checker
    fact_checker.add_tool(AILFToolAdapter(fact_check_tool))
    
    # Report writer - standard agent for summarizing findings
    report_writer = AILFEnabledAgent(
        name="ReportWriter",
        memory=shared_memory.kagent_memory,
        description="Specialized in creating clear, concise reports",
    )
    
    # Create the team
    team = Team(
        name="ResearchTeam",
        description="A team for researching topics and creating verified reports",
        members=[researcher, fact_checker, report_writer]
    )
    
    return team, shared_memory


async def main():
    # Create research team
    research_team, team_memory = await create_research_team()
    
    print(f"Created research team '{research_team.name}'")
    print("Team members:")
    for member in research_team.members:
        print(f"- {member.name}: {member.description}")
    
    # Task the team to research a topic
    print("\nExecuting team research task...")
    
    # Store the research topic in shared memory
    await team_memory.kagent_memory.set("research_topic", "renewable energy impacts")
    
    # Simulate workflow between agents
    
    # 1. Researcher gathers information
    researcher = research_team.get_member("Researcher")
    research_response = await researcher.run(
        "Research the latest information about renewable energy impacts on climate change"
    )
    print("\nResearcher findings:")
    print(research_response.messages[0].content)
    
    # Store findings in shared memory
    await team_memory.kagent_memory.set(
        "research_findings", 
        research_response.messages[0].content
    )
    
    # 2. Fact checker verifies key claims
    fact_checker = research_team.get_member("FactChecker")
    
    # Get the findings from memory
    findings = await team_memory.kagent_memory.get("research_findings")
    
    fact_check_response = await fact_checker.run(
        f"Verify the key claims in this research: {findings}"
    )
    print("\nFact Checker verification:")
    print(fact_check_response.messages[0].content)
    
    # Store verification in shared memory
    await team_memory.kagent_memory.set(
        "fact_check_results", 
        fact_check_response.messages[0].content
    )
    
    # 3. Report writer creates final report
    report_writer = research_team.get_member("ReportWriter")
    
    # Get all the information from memory
    topic = await team_memory.kagent_memory.get("research_topic")
    findings = await team_memory.kagent_memory.get("research_findings")
    verification = await team_memory.kagent_memory.get("fact_check_results")
    
    report_response = await report_writer.run(
        f"Create a concise report on {topic} based on these findings: {findings} "
        f"and this verification: {verification}"
    )
    print("\nFinal Report:")
    print(report_response.messages[0].content)
    
    # Export team memory for future reference
    await team_memory.export_to_json("research_team_memory.json")
    print("\nTeam memory exported to research_team_memory.json")


if __name__ == "__main__":
    asyncio.run(main())

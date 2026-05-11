from crewai import Agent
from crewai_tools import SerperDevTool


def destination_researcher_agent(llm) -> Agent:
    """
    Searches the web for destination-specific travel information:
    top attractions, hidden gems, visa requirements, local transport,
    cultural tips, and safety advice.
    """
    return Agent(
        role="Expert Travel Destination Researcher",
        goal=(
            "Research the destination thoroughly and provide a comprehensive "
            "overview including must-visit attractions, local culture, visa "
            "requirements, best areas to stay, and insider travel tips."
        ),
        backstory=(
            "You are a seasoned travel journalist who has visited over 80 countries. "
            "You have a knack for uncovering both iconic landmarks and hidden local gems. "
            "You always verify information from multiple sources and present it in a "
            "clear, traveller-friendly format."
        ),
        tools=[SerperDevTool()],
        llm=llm,
        verbose=True,
        allow_delegation=False,
        max_iter=2,        # FIX: hard cap at 2 searches — prevents token burst
        max_retry_limit=1,
    )
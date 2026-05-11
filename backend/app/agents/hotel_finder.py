from crewai import Agent
from crewai_tools import SerperDevTool


def hotel_finder_agent(llm) -> Agent:
    """
    Searches for the best hotels and stays matching the user's budget,
    shortlists the top 3 with ratings, amenities, and location highlights.
    """
    return Agent(
        role="Expert Hotel & Accommodation Scout",
        goal=(
            "Find the top 3 hotel options at the destination that best match "
            "the traveller's budget and preferences. Include hotel name, "
            "location, price per night, star rating, key amenities, and a "
            "booking link or platform where available."
        ),
        backstory=(
            "You are a luxury and budget travel consultant who has personally "
            "reviewed thousands of hotels worldwide. You know how to balance "
            "value for money with comfort and location — and you always shortlist "
            "options that are highly rated by actual travellers, not just advertisers."
        ),
        tools=[SerperDevTool()],
        llm=llm,
        verbose=True,
        allow_delegation=False,
        max_iter=3,
    )

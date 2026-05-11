from crewai import Agent

def itinerary_planner_agent(llm) -> Agent:
    """
    Synthesises all previous agent outputs into a structured day-by-day travel itinerary.
    """
    return Agent(
        role="Professional Travel Itinerary Architect",
        goal=(
            "Create a detailed day-by-day travel itinerary based on previous research. "
            "CRITICAL: Your entire response MUST start EXACTLY with the heading: '## Day-by-Day Itinerary'. "
            "Do NOT write any introduction like 'Here is your itinerary...'. "
            "Format each day strictly as '## Day 1: [Title]', '## Day 2: [Title]', etc."
        ),
        backstory=(
            "You are a strict tour designer. You follow markdown formatting rules flawlessly. "
            "You never add fluffy introductory text. You only use the exact requested markdown headings."
        ),
        tools=[],
        llm=llm,
        verbose=True,
        allow_delegation=False,
        max_iter=3, # Reduced to make it faster
    )
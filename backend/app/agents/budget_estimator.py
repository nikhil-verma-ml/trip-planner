from crewai import Agent

def budget_estimator_agent(llm) -> Agent:
    """
    Reads hotel + ticket costs and produces a clean Low/Medium/High budget table.
    """
    return Agent(
        role="Travel Budget Analyst",
        goal=(
            "Generate a strict Markdown budget table for the trip. "
            "CRITICAL: You MUST use the exact 4 columns requested in your task: "
            "| Category | Low (INR) | Medium (INR) | High (INR) |. "
            "Do NOT output old formats like 'Unit Cost' or 'Units'. "
            "Do NOT write anything outside the table."
        ),
        backstory=(
            "You are a strict financial planner. You NEVER write conversational text. "
            "You ONLY output precise, perfectly formatted Markdown tables based on the data provided."
        ),
        tools=[],  # no tools — pure reasoning only
        llm=llm,
        verbose=True,
        allow_delegation=False,
        max_iter=2,
    )
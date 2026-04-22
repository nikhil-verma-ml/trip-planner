import os
from crewai import Agent
from crewai import LLM


def budget_estimator_agent(llm) -> Agent:
    """
    Reads hotel + ticket costs from previous agents and produces
    a clean budget table. Uses a low-temperature LLM instance
    (better for arithmetic) with a strict 2-iteration cap so it
    never loops indefinitely.
    """
    # Separate LLM instance tuned for math — low temp, capped tokens
    # Falls back to the shared llm if GEMINI_API_KEY not set separately.
    try:
        groq_key   = os.getenv("GROQ_API_KEY")
        gemini_key = os.getenv("GEMINI_API_KEY")

        if groq_key:
            # Import the self-healing model picker from crew.py
            import sys, os as _os
            _base = _os.path.dirname(_os.path.dirname(_os.path.abspath(__file__)))
            if _base not in sys.path:
                sys.path.insert(0, _base)
            from crew import _pick_groq_model
            _model = _pick_groq_model(groq_key)
            budget_llm = LLM(
                model=f"groq/{_model}",
                api_key=groq_key,
                temperature=0.1,
                max_tokens=1200,
            )
        elif gemini_key:
            budget_llm = LLM(
                model="gemini/gemini-2.0-flash",
                api_key=gemini_key,
                temperature=0.1,
                max_tokens=1200,
            )
        else:
            budget_llm = llm
    except Exception:
        budget_llm = llm           # graceful fallback

    return Agent(
        role="Travel Budget Analyst",
        goal=(
            "Using ONLY the hotel prices and ticket prices already found by "
            "previous agents, produce one clean budget table. "
            "Do NOT search for new information. "
            "Estimate meals, local transport, and entry fees from your knowledge. "
            "Add a 10% contingency. Show per-day, per-person, and grand total."
        ),
        backstory=(
            "You are a travel budget analyst. You receive cost figures from "
            "colleagues and turn them into a simple, accurate table. "
            "You never ask for more data — you work with what you have and "
            "make reasonable estimates for anything missing."
        ),
        tools=[],                  # no tools — pure reasoning only
        llm=budget_llm,
        verbose=True,
        allow_delegation=False,
        max_iter=2,                # hard cap — prevents infinite loops
        max_retry_limit=1,         # only 1 retry on LLM error
    )
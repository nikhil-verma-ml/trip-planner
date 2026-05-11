import os
import sys
import logging
import pathlib
import time

log = logging.getLogger(__name__)

# ── Force local folders first in path ────────────────────────────────────────
_BASE = os.path.dirname(os.path.abspath(__file__))
if _BASE not in sys.path:
    sys.path.insert(0, _BASE)

from crewai import LLM
from agents.destination_researcher import destination_researcher_agent
from agents.weather_checker        import weather_checker_agent
from agents.hotel_finder           import hotel_finder_agent
from agents.ticket_finder          import ticket_finder_agent
from agents.itinerary_planner      import itinerary_planner_agent
from agents.budget_estimator       import budget_estimator_agent
from tasks.trip_tasks import create_all_tasks

def run_trip_planner(trip_details: dict) -> str:
    gemini_key = os.getenv("GEMINI_API_KEY")
    groq_key   = os.getenv("GROQ_API_KEY")

    if not gemini_key or not groq_key:
        raise ValueError("Bhai dono GEMINI_API_KEY aur GROQ_API_KEY .env me hone chahiye!")

    # Separate, isolated LLMs (No litellm fallback bug)
    gemini_llm = LLM(model="gemini/gemini-2.0-flash", api_key=gemini_key, temperature=0.7)
    groq_llm   = LLM(model="groq/llama-3.3-70b-versatile", api_key=groq_key, temperature=0.7)

    travel_mode = trip_details.get("travel_mode", "flight")

    # Instantiate agents with Gemini as default
    agents = {
        "researcher": destination_researcher_agent(gemini_llm),
        "weather":    weather_checker_agent(gemini_llm),
        "hotels":     hotel_finder_agent(gemini_llm),
        "tickets":    ticket_finder_agent(gemini_llm, travel_mode=travel_mode),
        "planner":    itinerary_planner_agent(gemini_llm),
        "budget":     budget_estimator_agent(gemini_llm),
    }

    tasks = create_all_tasks(agents, trip_details)
    pathlib.Path(os.path.join(_BASE, "output")).mkdir(parents=True, exist_ok=True)

    log.info("Starting safe sequential pipeline with Custom Ping-Pong Routing...")

    # Custom Execution Loop: Gemini -> Groq -> Wait -> Gemini
    for i, task in enumerate(tasks):
        agent = task.agent
        task_name = task.description.split()[0] # Just for logging
        log.info(f"--- Running Task {i+1}/6 ---")
        
        try:
            # First try: Gemini
            log.info(f"Attempting with Gemini...")
            agent.llm = gemini_llm
            result = task.execute_sync()
            task.output = result
            
        except Exception as e1:
            err_str = str(e1).lower()
            if "429" in err_str or "quota" in err_str or "rate limit" in err_str:
                log.warning("Gemini limit reached! Instantly switching to Groq...")
                try:
                    # Second try: Groq
                    agent.llm = groq_llm
                    result = task.execute_sync()
                    task.output = result
                    log.info("Groq successfully completed the task!")
                    
                except Exception as e2:
                    log.warning("Groq also failed. Sleeping for 60 seconds to reset Gemini limits...")
                    # Third try: Wait and back to Gemini
                    time.sleep(60)
                    log.info("Resuming with Gemini...")
                    agent.llm = gemini_llm
                    result = task.execute_sync()
                    task.output = result
            else:
                # Some other unknown error
                raise e1

    # Format the final output
    sections = [
        ("Destination Research",  tasks[0]),
        ("Weather Forecast",      tasks[1]),
        ("Hotel Recommendations", tasks[2]),
        ("Ticket Options",        tasks[3]),
        ("Day-by-Day Itinerary",  tasks[4]),
        ("Budget Breakdown",      tasks[5]),
    ]
    
    parts = []
    for title, task in sections:
        out = str(task.output).strip() if hasattr(task, "output") and task.output else ""
        if out:
            parts.append(f"## {title}\n\n{out}")

    final_str = "\n\n---\n\n".join(parts)
    
    with open(os.path.join(_BASE, "output", "crew_log.txt"), "w", encoding="utf-8") as f:
        f.write(final_str)

    return final_str if parts else "Pipeline completed — check output/crew_log.txt"
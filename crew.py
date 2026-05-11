import os
import sys
import logging
import pathlib
import time

log = logging.getLogger(__name__)

_BASE = os.path.dirname(os.path.abspath(__file__))
if _BASE not in sys.path:
    sys.path.insert(0, _BASE)

from crewai import Agent, Task, Crew, Process, LLM
from agents.destination_researcher import destination_researcher_agent
from agents.weather_checker        import weather_checker_agent
from agents.hotel_finder           import hotel_finder_agent
from agents.ticket_finder          import ticket_finder_agent
from agents.itinerary_planner      import itinerary_planner_agent
from agents.budget_estimator       import budget_estimator_agent
from tasks.trip_tasks              import create_all_tasks


def get_gemini():
    k = os.getenv("GEMINI_API_KEY", "")
    if not k.startswith("AIza"):
        log.warning("GEMINI_API_KEY invalid or missing — skipping")
        return None
    return LLM(model="gemini/gemini-2.0-flash", api_key=k, temperature=0.7)


def get_groq():
    k = os.getenv("GROQ_API_KEY", "")
    if not k.startswith("gsk_"):
        log.warning("GROQ_API_KEY invalid or missing — skipping")
        return None
    return LLM(model="groq/llama-3.3-70b-versatile", api_key=k, temperature=0.7)


def safe_execute(task: Task, agent: Agent, primary: LLM, fallback: LLM):
    """
    Try primary LLM → fallback LLM → wait 60s → retry fallback.
    Groq is primary (reliable), Gemini is fallback (quota limited).
    """
    for llm, label in [(primary, "Primary"), (fallback, "Fallback")]:
        if llm is None:
            continue
        try:
            agent.llm = llm
            result = task.execute_sync()
            task.output = result
            log.info(f"{label} ({llm.model}) succeeded.")
            return
        except Exception as e:
            log.warning(f"{label} ({llm.model}) failed: {str(e)[:80]}")

    # Both failed — wait and retry primary
    log.info("Both LLMs failed. Waiting 60s and retrying...")
    time.sleep(60)
    agent.llm = primary
    result = task.execute_sync()
    task.output = result


def run_trip_planner(trip_details: dict) -> str:
    gemini = get_gemini()
    groq   = get_groq()

    # Groq = primary (500K TPD, reliable)
    # Gemini = fallback (daily quota limited)
    primary  = groq   or gemini
    fallback = gemini if groq else None

    if primary is None:
        raise ValueError("No valid LLM found. Check GROQ_API_KEY and GEMINI_API_KEY in .env")

    log.info(f"Primary: {primary.model} | Fallback: {fallback.model if fallback else 'None'}")

    travel_mode = trip_details.get("travel_mode", "flight")

    agents = {
        "researcher": destination_researcher_agent(primary),
        "weather":    weather_checker_agent(primary),
        "hotels":     hotel_finder_agent(primary),
        "tickets":    ticket_finder_agent(primary, travel_mode=travel_mode),
        "planner":    itinerary_planner_agent(primary),
        "budget":     budget_estimator_agent(primary),
    }

    tasks = create_all_tasks(agents, trip_details)
    pathlib.Path(os.path.join(_BASE, "output")).mkdir(parents=True, exist_ok=True)

    log.info("Starting pipeline...")

    for i, task in enumerate(tasks):
        log.info(f"Phase {i+1}/6...")
        safe_execute(task, task.agent, primary, fallback)

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

    return "\n\n---\n\n".join(parts) if parts else "Pipeline completed."
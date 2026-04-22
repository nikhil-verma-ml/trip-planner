import os
import sys
import logging
log = logging.getLogger(__name__)

# ── Force local folders first in path ────────────────────────────────────────
# Fixes: "cannot import name 'X' from 'agents' (unknown location)"
# An installed package (crewai/langchain) ships a module also named 'agents',
# which shadows our local agents/ folder unless we prepend the project root.
_BASE = os.path.dirname(os.path.abspath(__file__))
if _BASE not in sys.path:
    sys.path.insert(0, _BASE)

# Now safe to import — Python resolves _BASE/agents/ first
from crewai import Crew, Process, LLM
from agents.destination_researcher import destination_researcher_agent
from agents.weather_checker        import weather_checker_agent
from agents.hotel_finder           import hotel_finder_agent
from agents.ticket_finder          import ticket_finder_agent
from agents.itinerary_planner      import itinerary_planner_agent
from agents.budget_estimator       import budget_estimator_agent
from tasks.trip_tasks import create_all_tasks


# ── Groq model priority list ─────────────────────────────────────────────────
# Ordered best → fallback. Auto-detection skips decommissioned models at runtime.
GROQ_MODEL_PRIORITY = [
    "llama-3.3-70b-versatile",   # best quality
    "llama-3.1-70b-versatile",   # fallback quality
    "llama-3.1-8b-instant",      # fast, lower TPM
    "llama3-8b-8192",            # legacy fallback
    "llama3-70b-8192",           # legacy fallback
]


def _pick_groq_model(api_key: str) -> str:
    """
    Query Groq /v1/models and return the first available model
    from GROQ_MODEL_PRIORITY. Falls back to first in list if API call fails.
    This means model deprecations are handled automatically at runtime.
    """
    try:
        import requests as _req
        resp = _req.get(
            "https://api.groq.com/openai/v1/models",
            headers={"Authorization": f"Bearer {api_key}"},
            timeout=8,
        )
        if resp.status_code == 200:
            live_ids = {m["id"] for m in resp.json().get("data", [])}
            log.info(f"Groq live models: {sorted(live_ids)}")
            for candidate in GROQ_MODEL_PRIORITY:
                if candidate in live_ids:
                    log.info(f"Selected Groq model: {candidate}")
                    return candidate
            # None of our list matched — use whatever is available
            if live_ids:
                chosen = sorted(live_ids)[0]
                log.warning(f"No priority model found, using: {chosen}")
                return chosen
    except Exception as e:
        log.warning(f"Could not fetch Groq model list: {e}")

    # Hard fallback — use first in priority list
    return GROQ_MODEL_PRIORITY[0]


def build_llm() -> LLM:
    """
    Build the LLM with self-healing model selection:
      1. Groq  — queries live model list, skips decommissioned models automatically
      2. Gemini — fallback if no GROQ_API_KEY
    """
    groq_key   = os.getenv("GROQ_API_KEY")
    gemini_key = os.getenv("GEMINI_API_KEY")

    if groq_key:
        model_name = _pick_groq_model(groq_key)
        log.info(f"LLM: Using groq/{model_name}")
        return LLM(
            model=f"groq/{model_name}",
            api_key=groq_key,
            temperature=0.7,
        )
    elif gemini_key:
        log.info("LLM: Using gemini/gemini-2.0-flash (fallback)")
        return LLM(
            model="gemini/gemini-2.0-flash",
            api_key=gemini_key,
            temperature=0.7,
        )
    else:
        raise ValueError(
            "No LLM API key found. Set GROQ_API_KEY or GEMINI_API_KEY in .env"
        )


def run_trip_planner(trip_details: dict) -> str:
    """
    Build and kick off the 6-agent trip planner crew.

    Args:
        trip_details : dict containing all trip parameters
                       (see main.py for full schema)

    Returns:
        str — the final combined travel guide output
    """
    llm = build_llm()
    travel_mode = trip_details.get("travel_mode", "flight")

    # ── Instantiate all 6 agents ──────────────────────────────────────────────
    agents = {
        "researcher": destination_researcher_agent(llm),
        "weather":    weather_checker_agent(llm),
        "hotels":     hotel_finder_agent(llm),
        "tickets":    ticket_finder_agent(llm, travel_mode=travel_mode),
        "planner":    itinerary_planner_agent(llm),
        "budget":     budget_estimator_agent(llm),
    }

    # ── Create all 6 tasks ────────────────────────────────────────────────────
    tasks = create_all_tasks(agents, trip_details)

    # ── Assemble the Crew ─────────────────────────────────────────────────────
    # ── Ensure output directory exists before crew starts ────────────────────
    import pathlib
    pathlib.Path("output").mkdir(parents=True, exist_ok=True)

    crew = Crew(
        agents=list(agents.values()),
        tasks=tasks,
        process=Process.sequential,
        verbose=True,
        memory=False,               # FIX: disable crew memory — reduces token bloat
        max_rpm=3,                  # FIX: paced to stay under Groq 20k TPM free limit
        output_log_file=os.path.join(_BASE, "output", "crew_log.txt"),
    )

    # ── Kick off and collect per-task outputs ─────────────────────────────────
    crew.kickoff()

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

    return "\n\n---\n\n".join(parts) if parts else "Pipeline completed — check output/crew_log.txt"
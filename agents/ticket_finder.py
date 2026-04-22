import os, sys as _sys
_sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from crewai import Agent
from tools.amadeus_tool import search_flights
from tools.railway_tool import search_trains


def ticket_finder_agent(llm, travel_mode: str = "flight") -> Agent:
    """
    Searches for cheapest flight or railway tickets depending on travel_mode.

    Args:
        llm         : The LLM instance to power this agent.
        travel_mode : 'flight' uses Amadeus API,
                      'train'  uses RailwayAPI (Indian Railways),
                      'both'   equips agent with both tools.
    """
    mode_map = {
        "flight": [search_flights],
        "train": [search_trains],
        "both": [search_flights, search_trains],
    }
    selected_tools = mode_map.get(travel_mode.lower(), [search_flights])

    mode_desc = {
        "flight": "flights using Amadeus API",
        "train": "trains using Indian Railways API",
        "both": "both flights (Amadeus) and trains (Indian Railways)",
    }.get(travel_mode.lower(), "flights")

    return Agent(
        role="Smart Ticket Price Comparison Expert",
        goal=(
            f"Search for the cheapest and most convenient {mode_desc} for the "
            "given route and date. Compare options by price, journey duration, "
            "and comfort level. Return the top 3 deals with all relevant details "
            "so the traveller can make an informed booking decision."
        ),
        backstory=(
            "You are a travel-tech expert who has built fare-comparison engines "
            "for major travel portals. You understand that price is not the only "
            "factor — journey duration, number of stops, and departure times "
            "matter just as much. You always present options clearly so "
            "travellers can choose what suits them best."
        ),
        tools=selected_tools,
        llm=llm,
        verbose=True,
        allow_delegation=False,
        max_iter=3,
    )

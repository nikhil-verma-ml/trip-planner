import os, sys as _sys
_sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from crewai import Agent
from tools.weather_tool import get_weather_forecast


def weather_checker_agent(llm) -> Agent:
    """
    Fetches a 5-day weather forecast for the destination and provides
    packing advice and best-time-of-day recommendations.
    """
    return Agent(
        role="Meteorologist & Travel Weather Advisor",
        goal=(
            "Fetch the weather forecast for the travel destination and dates, "
            "then give practical advice on what to pack, best times for outdoor "
            "activities, and any weather-related warnings the traveller should know."
        ),
        backstory=(
            "You are a certified meteorologist who specialises in travel weather "
            "advisory. You translate raw forecast data into simple, actionable "
            "guidance so travellers are never caught off guard by the weather."
        ),
        tools=[get_weather_forecast],
        llm=llm,
        verbose=True,
        allow_delegation=False,
        max_iter=2,
    )

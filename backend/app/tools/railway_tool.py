import os
import requests
from crewai.tools import tool


@tool("Train Search Tool")
def search_trains(origin_station: str, destination_station: str, date: str) -> str:
    """
    Search for available trains between two Indian railway stations using RailwayAPI
    (free tier on RapidAPI — 500 calls/month).

    Args:
        origin_station      : Station code or name (e.g. 'NDLS' for New Delhi,
                              'BCT' for Mumbai Central, 'MAS' for Chennai Central)
        destination_station : Destination station code or name (e.g. 'HWH' for Howrah)
        date                : Travel date in YYYYMMDD format (e.g. '20250915')

    Returns top 3 available trains with train number, name, departure/arrival times,
    journey duration, and fare for Sleeper and 3AC classes.
    """
    api_key = os.getenv("RAPIDAPI_KEY")
    if not api_key:
        return "Error: RAPIDAPI_KEY not set in .env"

    url = "https://indian-railway-irctc.p.rapidapi.com/api/trains-search/v1/train"
    headers = {
        "x-rapidapi-host": "indian-railway-irctc.p.rapidapi.com",
        "x-rapidapi-key": api_key,
        "x-rapid-api": "rapid-api-database",
    }
    params = {
        "fromStationCode": origin_station.upper(),
        "toStationCode": destination_station.upper(),
        "dateOfJourney": date,  # YYYYMMDD
    }

    try:
        resp = requests.get(url, headers=headers, params=params, timeout=15)
    except requests.exceptions.RequestException as e:
        return f"Network error calling RailwayAPI: {e}"

    if resp.status_code != 200:
        return f"RailwayAPI error ({resp.status_code}): {resp.text[:300]}"

    trains = resp.json().get("body", {}).get("trainsList", [])
    if not trains:
        return (
            f"No trains found from {origin_station} to {destination_station} "
            f"on {date}. Check station codes and date."
        )

    lines = [
        f"Top Train Options — {origin_station.upper()} → "
        f"{destination_station.upper()} on {date}:\n"
    ]

    for i, train in enumerate(trains[:3], 1):
        train_no = train.get("trainNumber", "N/A")
        train_name = train.get("trainName", "N/A").title()
        dep = train.get("departureTime", "N/A")
        arr = train.get("arrivalTime", "N/A")
        duration = train.get("duration", "N/A")
        run_days = ", ".join(train.get("runningDays", []))

        # Fare info (if available in response)
        fares = train.get("fare", {})
        sl_fare = fares.get("SL", "N/A")
        ac3_fare = fares.get("3A", "N/A")

        lines.append(
            f"  {i}. 🚆 {train_no} — {train_name}\n"
            f"     Dep: {dep} | Arr: {arr} | Duration: {duration}\n"
            f"     Runs on: {run_days}\n"
            f"     Fare → Sleeper (SL): ₹{sl_fare} | 3AC (3A): ₹{ac3_fare}"
        )

    return "\n".join(lines)

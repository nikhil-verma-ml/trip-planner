"""
Flight Search Tool — Updated (Amadeus deprecated July 2026)

Uses Serper API to query Google Flights results.
No extra API key needed — reuses SERPER_API_KEY already in .env.

Fallback: Aviationstack API (100 free calls/month → aviationstack.com)
"""

import os
import requests
from crewai.tools import tool


def _search_via_serper(origin: str, destination: str, date: str, adults: int) -> str:
    """Search Google Flights using Serper's search API."""
    api_key = os.getenv("SERPER_API_KEY")
    if not api_key:
        return "Error: SERPER_API_KEY not set in .env"

    query = (
        f"cheapest flights from {origin} to {destination} "
        f"on {date} for {adults} passenger economy class price INR"
    )

    url = "https://google.serper.dev/search"
    headers = {"X-API-KEY": api_key, "Content-Type": "application/json"}
    payload = {"q": query, "num": 8, "gl": "in", "hl": "en"}

    resp = requests.post(url, headers=headers, json=payload, timeout=15)
    if resp.status_code != 200:
        return f"Serper API error ({resp.status_code}): {resp.text[:300]}"

    data = resp.json()
    lines = [f"Flight Search Results — {origin.upper()} → {destination.upper()} on {date}:\n"]

    if "answerBox" in data:
        snippet = data["answerBox"].get("answer") or data["answerBox"].get("snippet", "")
        if snippet:
            lines.append(f"  Google Flights Summary:\n  {snippet}\n")

    flight_keywords = ["flight", "airline", "fare", "ticket", "air india",
                       "indigo", "spicejet", "emirates", "qatar", "rs.", "inr", "₹"]
    found = 0
    for item in data.get("organic", []):
        title   = item.get("title", "")
        snippet = item.get("snippet", "")
        link    = item.get("link", "")
        if any(kw in (title + snippet).lower() for kw in flight_keywords) and found < 4:
            lines.append(f"  {found+1}. {title}")
            if snippet:
                lines.append(f"     {snippet[:180]}")
            if link:
                lines.append(f"     {link}")
            lines.append("")
            found += 1

    if found == 0:
        lines.append(
            f"  No direct results found. Search manually:\n"
            f"  google.com/flights | makemytrip.com | skyscanner.co.in\n"
            f"  Route: {origin.upper()} to {destination.upper()} on {date}"
        )

    lines.append("\n  Compare & book: makemytrip.com | goibibo.com | skyscanner.co.in")
    return "\n".join(lines)


def _search_via_aviationstack(origin: str, destination: str, date: str) -> str:
    """Fallback: Aviationstack free tier (100 calls/month — aviationstack.com)"""
    api_key = os.getenv("AVIATIONSTACK_API_KEY")
    if not api_key:
        return None

    url = "http://api.aviationstack.com/v1/flights"
    params = {
        "access_key": api_key,
        "dep_iata": origin.upper(),
        "arr_iata": destination.upper(),
        "flight_date": date,
        "flight_status": "scheduled",
        "limit": 5,
    }
    try:
        resp = requests.get(url, params=params, timeout=15)
        if resp.status_code != 200:
            return None
        data = resp.json().get("data", [])
        if not data:
            return None

        lines = [f"Scheduled Flights — {origin.upper()} to {destination.upper()} on {date}:\n"]
        for i, f in enumerate(data[:3], 1):
            airline  = f.get("airline", {}).get("name", "N/A")
            fno      = f.get("flight", {}).get("iata", "N/A")
            dep      = f.get("departure", {}).get("scheduled", "N/A")[11:16]
            arr      = f.get("arrival", {}).get("scheduled", "N/A")[11:16]
            lines.append(f"  {i}. {airline} {fno} | Dep: {dep} → Arr: {arr}")

        lines.append("\n  For fares: makemytrip.com / skyscanner.co.in")
        return "\n".join(lines)
    except Exception:
        return None


@tool("Flight Search Tool")
def search_flights(origin: str, destination: str, date: str, adults: int = 1) -> str:
    """
    Search for available flights between two cities.

    Args:
        origin      : IATA airport code (e.g. 'DEL', 'BOM', 'BLR')
        destination : IATA airport code (e.g. 'LHR', 'JFK', 'DXB')
        date        : Departure date in YYYY-MM-DD format
        adults      : Number of passengers (default 1)

    Provider priority:
      1. Aviationstack API (if AVIATIONSTACK_API_KEY set — free 100 calls/month)
      2. Serper API Google Flights search (uses existing SERPER_API_KEY)
    """
    result = _search_via_aviationstack(origin, destination, date)
    return result if result else _search_via_serper(origin, destination, date, adults)

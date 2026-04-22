"""
╔══════════════════════════════════════════════════════╗
║         AI Trip Planner — 6-Agent CrewAI Pipeline    ║
║   Powered by: Gemini | Serper | Amadeus | RapidAPI   ║
╚══════════════════════════════════════════════════════╝

Usage:
    python main.py

Make sure you have copied .env.example → .env and filled
in all API keys before running.
"""

import os
import sys

# ── Force project root into sys.path ─────────────────────────────────────────
_BASE = os.path.dirname(os.path.abspath(__file__))
if _BASE not in sys.path:
    sys.path.insert(0, _BASE)

from datetime import datetime
from dotenv import load_dotenv
from crew import run_trip_planner

load_dotenv()


# ── Helpers ───────────────────────────────────────────────────────────────────

def check_env_keys():
    """Warn about any missing API keys before starting."""
    required = {
        "GEMINI_API_KEY":       "Gemini (aistudio.google.com)",
        "SERPER_API_KEY":       "Serper (serper.dev)",
        "OPENWEATHER_API_KEY":  "OpenWeather (openweathermap.org)",
    }
    optional = {
        "AMADEUS_CLIENT_ID":    "Amadeus — needed for flight search",
        "AMADEUS_CLIENT_SECRET":"Amadeus — needed for flight search",
        "RAPIDAPI_KEY":         "RapidAPI — needed for train search",
    }
    missing_required = [f"  ✗ {k} ({src})" for k, src in required.items() if not os.getenv(k)]
    missing_optional = [f"  ! {k} ({src})" for k, src in optional.items() if not os.getenv(k)]

    if missing_required:
        print("\n[ERROR] Missing required API keys in .env:")
        print("\n".join(missing_required))
        print("\nCopy .env.example → .env and fill in your keys, then re-run.\n")
        sys.exit(1)

    if missing_optional:
        print("\n[WARNING] Optional keys not set (some features may be limited):")
        print("\n".join(missing_optional))
        print()


def prompt(label: str, default: str = "") -> str:
    """Prompt user for input with an optional default value."""
    default_hint = f" [{default}]" if default else ""
    value = input(f"  {label}{default_hint}: ").strip()
    return value if value else default


def collect_trip_details() -> dict:
    """Interactive CLI to collect all trip parameters from the user."""
    print("\n" + "═" * 56)
    print("  🌍  AI Trip Planner — Enter Your Trip Details")
    print("═" * 56 + "\n")

    destination  = prompt("Destination city / country", "Paris, France")
    origin_city  = prompt("Your departure city", "New Delhi")
    travel_dates = prompt("Travel dates (e.g. 15 Sep 2025 – 22 Sep 2025)", "15 Sep 2025 – 22 Sep 2025")
    num_str      = prompt("Number of travellers", "2")
    budget_str   = prompt("Total budget in INR (₹)", "150000")
    interests    = prompt("Interests / preferences", "history, food, art, local markets")

    print("\n  Travel mode options:")
    print("    1 → Flight  (uses Amadeus API)")
    print("    2 → Train   (uses RailwayAPI — Indian Railways)")
    print("    3 → Both    (compare flight vs train)")
    mode_choice  = prompt("Choose travel mode (1/2/3)", "1")
    mode_map     = {"1": "flight", "2": "train", "3": "both"}
    travel_mode  = mode_map.get(mode_choice, "flight")

    # Extra fields depending on mode
    origin_iata = dest_iata = origin_station = dest_station = ""
    date_yyyymmdd = datetime.now().strftime("%Y%m%d")

    if travel_mode in ("flight", "both"):
        print("\n  Flight details (IATA airport codes):")
        origin_iata   = prompt("Origin IATA code", "DEL").upper()
        dest_iata     = prompt("Destination IATA code", "CDG").upper()
        date_raw      = prompt("Departure date (YYYY-MM-DD)", "2025-09-15")
        date_yyyymmdd = date_raw.replace("-", "")

    if travel_mode in ("train", "both"):
        print("\n  Train details (Indian Railways station codes):")
        origin_station = prompt("Origin station code", "NDLS").upper()
        dest_station   = prompt("Destination station code", "BCT").upper()
        if not date_yyyymmdd or date_yyyymmdd == datetime.now().strftime("%Y%m%d"):
            date_raw      = prompt("Departure date (YYYYMMDD)", "20250915")
            date_yyyymmdd = date_raw.replace("-", "")

    return {
        "destination":    destination,
        "origin_city":    origin_city,
        "travel_dates":   travel_dates,
        "num_travellers": int(num_str) if num_str.isdigit() else 2,
        "budget_inr":     int(budget_str.replace(",", "")) if budget_str.replace(",", "").isdigit() else 150000,
        "interests":      interests,
        "travel_mode":    travel_mode,
        "origin_iata":    origin_iata,
        "dest_iata":      dest_iata,
        "origin_station": origin_station,
        "dest_station":   dest_station,
        "date_yyyymmdd":  date_yyyymmdd,
    }


def save_output(result: str, destination: str):
    """Save the final travel guide to the output/ folder."""
    os.makedirs(os.path.join(_BASE, "output"), exist_ok=True)
    safe_name = destination.replace(",", "").replace(" ", "_").lower()
    timestamp  = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename   = os.path.join(_BASE, "output", f"travel_guide_{safe_name}_{timestamp}.md")

    with open(filename, "w", encoding="utf-8") as f:
        f.write(f"# AI Travel Guide — {destination}\n\n")
        f.write(result)

    print(f"\n  ✅ Travel guide saved to: {filename}\n")
    return filename


# ── Entry Point ───────────────────────────────────────────────────────────────

def main():
    check_env_keys()
    trip_details = collect_trip_details()

    print("\n" + "═" * 56)
    print("  🚀 Launching 6-Agent CrewAI Pipeline…")
    print("═" * 56)
    print(f"\n  Destination : {trip_details['destination']}")
    print(f"  From        : {trip_details['origin_city']}")
    print(f"  Dates       : {trip_details['travel_dates']}")
    print(f"  Travellers  : {trip_details['num_travellers']}")
    print(f"  Budget      : ₹{trip_details['budget_inr']:,}")
    print(f"  Mode        : {trip_details['travel_mode'].title()}")
    print("\n  Agents running sequentially — this may take 2–5 minutes…\n")

    result = run_trip_planner(trip_details)

    print("\n" + "═" * 56)
    print("  ✈  YOUR PERSONALISED TRAVEL GUIDE IS READY")
    print("═" * 56 + "\n")
    print(result)

    save_output(result, trip_details["destination"])


if __name__ == "__main__":
    main()
# AI Trip Planner — 6-Agent CrewAI Pipeline

A fully agentic trip planning system built with **CrewAI** that automatically
researches destinations, checks weather, finds hotels, searches for the cheapest
flight or train tickets, builds a day-by-day itinerary, and estimates your total
budget — all using **free APIs only**.

---

## Agents at a Glance

| # | Agent | API Used | Purpose |
|---|-------|----------|---------|
| 1 | Destination Researcher | Serper + Gemini | Attractions, food, visa, tips |
| 2 | Weather Checker | OpenWeather + Gemini | 5-day forecast & packing list |
| 3 | Hotel Finder | Serper + Gemini | Top 3 hotels within budget |
| 4 | Ticket Price Finder | Amadeus / RailwayAPI | Cheapest flights or trains |
| 5 | Itinerary Planner | Gemini | Day-by-day schedule |
| 6 | Budget Estimator | Gemini | Full cost breakdown |

---

## File Structure

```
trip_planner/
├── main.py                  ← Entry point (run this)
├── crew.py                  ← Assembles agents + tasks into CrewAI Crew
├── requirements.txt         ← Python dependencies
├── .env.example             ← API key template (copy → .env)
│
├── agents/
│   ├── __init__.py
│   ├── destination_researcher.py
│   ├── weather_checker.py
│   ├── hotel_finder.py
│   ├── ticket_finder.py     ← Supports flight / train / both
│   ├── itinerary_planner.py
│   └── budget_estimator.py
│
├── tasks/
│   ├── __init__.py
│   └── trip_tasks.py        ← All 6 task definitions with context chaining
│
├── tools/
│   ├── __init__.py
│   ├── weather_tool.py      ← OpenWeather API wrapper (@tool)
│   ├── amadeus_tool.py      ← Amadeus flight search wrapper (@tool)
│   └── railway_tool.py      ← Indian Railways RapidAPI wrapper (@tool)
│
└── output/                  ← Generated travel guides saved here
    └── travel_guide_*.md
```

---

## Quickstart

### 1. Clone / download the project

```bash
cd trip_planner
```

### 2. Create a virtual environment

```bash
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Set up API keys

```bash
cp .env.example .env
```

Open `.env` and fill in your free API keys:

| Key | Where to Get |
|-----|-------------|
| `GEMINI_API_KEY` | [aistudio.google.com](https://aistudio.google.com) |
| `SERPER_API_KEY` | [serper.dev](https://serper.dev) — 2,500 free searches/mo |
| `OPENWEATHER_API_KEY` | [openweathermap.org](https://openweathermap.org/api) |
| `AMADEUS_CLIENT_ID` + `SECRET` | [developers.amadeus.com](https://developers.amadeus.com) |
| `RAPIDAPI_KEY` | [rapidapi.com](https://rapidapi.com) → search "indian railway" |

### 5. Run the planner

```bash
python main.py
```

The CLI will ask for destination, dates, budget, and travel mode.
The crew runs sequentially (~2–5 minutes) and saves a `.md` travel guide in `output/`.

---

## Example Input

```
Destination         : Paris, France
Departure city      : New Delhi
Travel dates        : 15 Sep 2025 – 22 Sep 2025
Travellers          : 2
Budget              : ₹2,50,000
Interests           : art, food, history, local markets
Travel mode         : Flight
Origin IATA         : DEL
Destination IATA    : CDG
Departure date      : 2025-09-15
```

## Example Output (saved to output/)

```
# AI Travel Guide — Paris, France

## Destination Overview
...

## Weather Forecast
...

## Hotel Recommendations
...

## Best Flight Deals
...

## Day-by-Day Itinerary
Day 1 — Arrival & Montmartre
  🌅 Morning  : Land at CDG, check into hotel (~1.5 hr)
  ☀  Afternoon : Walk Montmartre, visit Sacré-Cœur
  🌙 Evening  : Dinner at a local bistro on Rue Lepic
...

## Budget Breakdown
| Category         | Total (₹)  |
|-----------------|-----------|
| Flights (×2)    | 64,800    |
| Hotel (7 nights)| 84,000    |
| Food (7 days)   | 28,000    |
| Transport       | 8,400     |
| Activities      | 12,600    |
| Contingency 10% | 19,780    |
| **Grand Total** | **2,17,580** |
```

---

## Notes

- Amadeus uses the **test environment** by default (indicative prices, not bookable).
  To switch to live: change `test.api.amadeus.com` → `api.amadeus.com` in `amadeus_tool.py`.
- RailwayAPI free tier allows **500 calls/month** on RapidAPI.
- All agent outputs are chained via CrewAI's `context` parameter, so each agent
  has full access to what the previous agents discovered.

---

## Tech Stack

- **CrewAI** — multi-agent orchestration
- **LangChain Google GenAI** — Gemini 1.5 Flash LLM (free)
- **SerperDevTool** — web search (built into crewai-tools)
- **Amadeus Python SDK** — flight search
- **Requests** — OpenWeather + RailwayAPI HTTP calls
- **python-dotenv** — environment variable management

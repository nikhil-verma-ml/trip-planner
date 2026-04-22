from crewai import Task


def create_all_tasks(agents: dict, trip_details: dict) -> list[Task]:
    """
    Create all 6 tasks for the trip planner pipeline.

    Args:
        agents      : dict of agent instances keyed by name
        trip_details: dict with keys:
                        destination, origin_city, travel_dates,
                        budget_inr, num_travellers, interests,
                        travel_mode, origin_iata, dest_iata,
                        origin_station, dest_station, date_yyyymmdd

    Returns list of Task objects in sequential order.
    """
    d = trip_details

    # ── Task 1: Destination Research ─────────────────────────────────────────
    # ── Task 1: Destination Research (shortened to reduce Groq TPM usage) ────
    task_research = Task(
        description=(
            f"Research {d['destination']} for a traveller interested in: {d['interests']}.\n"
            "Do ONE search then write a concise brief covering:\n"
            "- Top 5 attractions (1 line each)\n"
            "- 2 local hidden gems\n"
            "- Best area to stay\n"
            "- 3 dishes to try\n"
            "- Visa info for Indian passport holders\n"
            "- Transport options (metro/bus/taxi)\n"
            "- 2 cultural etiquette tips\n"
            "Keep response under 350 words. Be concise."
        ),
        expected_output=(
            "Destination brief under 350 words. Bullet points. "
            "Sections: Attractions, Food, Transport, Visa, Tips."
        ),
        agent=agents["researcher"],
    )

    # ── Task 2: Weather Check ─────────────────────────────────────────────────
    task_weather = Task(
        description=(
            f"Fetch the 5-day weather forecast for **{d['destination']}** "
            f"covering the travel dates: **{d['travel_dates']}**.\n\n"
            "Use the Weather Forecast Tool with the city name.\n\n"
            "Based on the forecast:\n"
            "1. Summarise the weather for each day\n"
            "2. Recommend the best times for outdoor activities\n"
            "3. List essential items to pack (clothing, gear)\n"
            "4. Highlight any weather warnings or considerations"
        ),
        expected_output=(
            "A day-by-day weather summary table followed by a packing checklist "
            "and outdoor activity timing recommendations. Keep it concise and practical."
        ),
        agent=agents["weather"],
        context=[task_research],
    )

    # ── Task 3: Hotel Search ──────────────────────────────────────────────────
    task_hotels = Task(
        description=(
            f"Find the top 3 hotel options in **{d['destination']}** "
            f"for **{d['num_travellers']} traveller(s)** "
            f"with a total accommodation budget of **₹{d['budget_inr']:,}** "
            f"for the trip duration: **{d['travel_dates']}**.\n\n"
            "Search for hotels using web search. For each hotel, provide:\n"
            "1. Hotel name and star rating\n"
            "2. Location / neighbourhood\n"
            "3. Price per night (approx.)\n"
            "4. Key amenities (WiFi, breakfast, pool, AC, etc.)\n"
            "5. Guest rating (out of 10 or 5)\n"
            "6. Booking platform (Booking.com / MakeMyTrip / Hotels.com)\n"
            "7. Why it's a good fit for this traveller"
        ),
        expected_output=(
            "A comparison of 3 hotels formatted as separate numbered sections, "
            "each with all the details listed above. End with a recommended pick "
            "and a brief reason why."
        ),
        agent=agents["hotels"],
        context=[task_research],
    )

    # ── Task 4: Ticket Search ─────────────────────────────────────────────────
    if d["travel_mode"] == "flight":
        ticket_desc = (
            f"Search for the cheapest available flights from "
            f"**{d['origin_city']}** ({d['origin_iata']}) to "
            f"**{d['destination']}** ({d['dest_iata']}) "
            f"on **{d['date_yyyymmdd'][:4]}-{d['date_yyyymmdd'][4:6]}-{d['date_yyyymmdd'][6:]}** "
            f"for **{d['num_travellers']} adult(s)**.\n\n"
            "Use the Flight Search Tool with IATA codes.\n"
            "Compare the top 3 results by:\n"
            "1. Total price (INR)\n"
            "2. Journey duration\n"
            "3. Number of stops\n"
            "4. Departure and arrival times\n"
            "5. Airline and flight number\n\n"
            "Recommend the best value option with reasoning."
        )
    elif d["travel_mode"] == "train":
        ticket_desc = (
            f"Search for the best trains from "
            f"**{d['origin_city']}** ({d['origin_station']}) to "
            f"**{d['destination']}** ({d['dest_station']}) "
            f"on **{d['date_yyyymmdd']}** for **{d['num_travellers']} passenger(s)**.\n\n"
            "Use the Train Search Tool with station codes.\n"
            "Compare the top 3 trains by:\n"
            "1. Fare for Sleeper (SL) and 3AC (3A) classes\n"
            "2. Journey duration\n"
            "3. Departure and arrival times\n"
            "4. Days of operation\n\n"
            "Recommend the best option with reasoning."
        )
    else:  # both
        ticket_desc = (
            f"Search for BOTH flights and trains from **{d['origin_city']}** "
            f"to **{d['destination']}** on **{d['date_yyyymmdd']}**.\n\n"
            f"Flights: Use IATA codes {d['origin_iata']} → {d['dest_iata']}.\n"
            f"Trains: Use station codes {d['origin_station']} → {d['dest_station']}.\n\n"
            "Compare top 3 options for each mode. Then provide a final recommendation "
            "on which mode of travel is best for this trip considering price, time, and comfort."
        )

    task_tickets = Task(
        description=ticket_desc,
        expected_output=(
            "A structured comparison of the top 3 ticket options with all details. "
            "End with a clear recommendation (Best Pick) and total ticket cost "
            "for all travellers."
        ),
        agent=agents["tickets"],
        context=[task_research],
    )

    # ── Task 5: Itinerary Planning ────────────────────────────────────────────
    task_itinerary = Task(
        description=(
            f"Create a detailed day-by-day travel itinerary for **{d['destination']}** "
            f"for **{d['num_travellers']} traveller(s)** over the trip: **{d['travel_dates']}**.\n\n"
            "Use ALL context from previous tasks:\n"
            "- Destination research (attractions, food, transport)\n"
            "- Weather forecast (best times, what to carry)\n"
            "- Hotel info (check-in/check-out, location)\n"
            "- Ticket info (departure/arrival times affect Day 1 and last day)\n\n"
            "For each day provide:\n"
            "  🌅 Morning  — activity + location + travel time\n"
            "  ☀ Afternoon — activity + meal suggestion + travel time\n"
            "  🌙 Evening  — activity or leisure + dinner recommendation\n\n"
            "Also include:\n"
            "- Day 1: arrival, check-in, light exploration\n"
            "- Last day: checkout, final activity, departure\n"
            "- Practical tips for each day"
        ),
        expected_output=(
            "A complete day-by-day itinerary with morning/afternoon/evening breakdown "
            "for every day of the trip. Format each day as a clear section. "
            "Include timing estimates, travel tips, and meal suggestions throughout."
        ),
        agent=agents["planner"],
        context=[task_research, task_hotels, task_tickets],  # FIX: task_weather removed — reduces context size
    )

    # ── Task 6: Budget Estimation ─────────────────────────────────────────────
    # FIX: task_itinerary removed from context — too large, causes LLM stall.
    # Key trip numbers are embedded directly in the description instead.
    task_budget = Task(
        description=(
            f"Create a budget breakdown for this trip:\n"
            f"  Destination  : {d['destination']}\n"
            f"  Duration     : {d['travel_dates']}\n"
            f"  Travellers   : {d['num_travellers']}\n"
            f"  Total budget : INR {d['budget_inr']:,}\n\n"
            "STEP 1 — From the Hotel Finder context, extract: hotel name + price per night.\n"
            "STEP 2 — From the Ticket Finder context, extract: total ticket cost per person.\n"
            "STEP 3 — Estimate from your knowledge of the destination:\n"
            "  - Daily meals per person (breakfast + lunch + dinner)\n"
            "  - Local transport per day (metro / taxi / auto)\n"
            "  - Entry fees for 3 major attractions (total)\n"
            "  - Miscellaneous (SIM, tips, incidentals)\n\n"
            "STEP 4 — Write ONE markdown table with columns:\n"
            "  Category | Unit Cost (INR) | Units | Total (INR)\n"
            "  Rows: Flights/Trains, Hotel, Meals, Local Transport, Attractions, Misc\n\n"
            "STEP 5 — Below the table write:\n"
            "  Subtotal, +10pct Contingency, Grand Total\n"
            f"  Budget status vs INR {d['budget_inr']:,} (within budget or over by how much)\n\n"
            "IMPORTANT: Keep response under 350 words. "
            "No day-by-day plans. Numbers and table only."
        ),
        expected_output=(
            "A markdown table (Category | Unit Cost | Units | Total) "
            "with subtotal, 10pct contingency, grand total, and one-line budget status. "
            "Maximum 350 words."
        ),
        agent=agents["budget"],
        context=[task_hotels, task_tickets],
    )

    return [
        task_research,
        task_weather,
        task_hotels,
        task_tickets,
        task_itinerary,
        task_budget,
    ]
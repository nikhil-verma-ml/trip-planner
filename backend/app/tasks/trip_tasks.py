from crewai import Task

def create_all_tasks(agents: dict, trip_details: dict) -> list[Task]:
    d = trip_details

    # ── Task 1: Destination Research ─────────────────────────────────────────
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
        expected_output="Destination brief under 350 words. Bullet points. Sections: Attractions, Food, Transport, Visa, Tips.",
        agent=agents["researcher"],
    )

    # ── Task 2: Weather Check ─────────────────────────────────────────────────
    task_weather = Task(
        description=(
            f"Fetch the 5-day weather forecast for **{d['destination']}** covering dates: **{d['travel_dates']}**.\n\n"
            "CRITICAL FORMATTING: You MUST output a Markdown table with the columns: | Day | Condition | Temp Range | Humidity |\n"
            "Below the table, provide a 'Packing Checklist' using bullet points."
        ),
        expected_output="A weather markdown table and a packing checklist.",
        agent=agents["weather"],
        context=[task_research],
    )

    # ── Task 3: Hotel Search ──────────────────────────────────────────────────
    task_hotels = Task(
        description=(
            f"Find the top 3 hotel options in **{d['destination']}** for **{d['num_travellers']} traveller(s)** "
            f"with a budget of **₹{d['budget_inr']:,}** for **{d['travel_dates']}**.\n\n"
            "CRITICAL FORMATTING: You MUST list EXACTLY 3 hotels. Each hotel MUST strictly start with a number like this:\n\n"
            "1. Hotel Name: [Name] ([Star]-star)\n"
            "Location: [Address]\n"
            "Price: ₹[Price per night]\n"
            "Amenities: [List]\n"
            "Guest rating: [Rating]/10\n"
            "Why it's a good fit: [Reason]\n\n"
            "Repeat for 2. and 3. Then give a 'Recommended Pick'."
        ),
        expected_output="3 strictly numbered hotel options with details, followed by a recommendation.",
        agent=agents["hotels"],
        context=[task_research],
    )

    # ── Task 4: Ticket Search ─────────────────────────────────────────────────
    mode = d["travel_mode"]
    ticket_desc = (
        f"Search for cheapest {mode} from {d['origin_city']} to {d['destination']} on {d['date_yyyymmdd']} for {d['num_travellers']} adults.\n\n"
        "CRITICAL FORMATTING: You MUST output exactly 3 options. Each option MUST start with a number exactly like this:\n\n"
        "1. Airline/Train: [Name] | Duration: [Xh] | Price: ₹[Total Price] | Times: [Dep-Arr] | Stops: [Stops]\n"
        "2. Airline/Train: [Name] | Duration: [Xh] | Price: ₹[Total Price] | Times: [Dep-Arr] | Stops: [Stops]\n"
        "3. Airline/Train: [Name] | Duration: [Xh] | Price: ₹[Total Price] | Times: [Dep-Arr] | Stops: [Stops]\n\n"
        "Then write 'Best Pick: [Your choice]'."
    )
    task_tickets = Task(
        description=ticket_desc,
        expected_output="3 strictly numbered ticket options in a single line each, followed by a Best Pick.",
        agent=agents["tickets"],
        context=[task_research],
    )

    # ── Task 5: Itinerary Planning ────────────────────────────────────────────
    task_itinerary = Task(
        description=(
            f"Create a day-by-day itinerary for {d['destination']} for {d['travel_dates']}.\n\n"
            "CRITICAL FORMATTING: You MUST start your response with '## Day-by-Day Itinerary'.\n"
            "Then, you MUST format each day EXACTLY like this (including emojis):\n\n"
            "## Day 1: [Title]\n"
            "🌅 Morning: [Details]\n"
            "☀ Afternoon: [Details]\n"
            "🌙 Evening: [Details]\n"
            "💡 Practical Tips: [Tips]\n\n"
            "Do this for every single day of the trip."
        ),
        expected_output="A strictly formatted day-by-day itinerary with emojis.",
        agent=agents["planner"],
        context=[task_research, task_hotels, task_tickets],
    )

    # ── Task 6: Budget Estimation (Low, Medium, High) ─────────────────────────
    task_budget = Task(
        description=(
            f"Create a budget breakdown for {d['destination']} ({d['travel_dates']} for {d['num_travellers']} pax).\n"
            f"The user requested Low, Medium, and High budget estimates. Target baseline is ₹{d['budget_inr']:,}.\n\n"
            "CRITICAL FORMATTING: You MUST output ONE Markdown table EXACTLY like this:\n\n"
            "| Category | Low (INR) | Medium (INR) | High (INR) |\n"
            "|---|---|---|---|\n"
            "| Flights/Trains | [Amt] | [Amt] | [Amt] |\n"
            "| Hotel (Total) | [Amt] | [Amt] | [Amt] |\n"
            "| Meals | [Amt] | [Amt] | [Amt] |\n"
            "| Local Transport | [Amt] | [Amt] | [Amt] |\n"
            "| Attractions | [Amt] | [Amt] | [Amt] |\n"
            "| Misc | [Amt] | [Amt] | [Amt] |\n"
            "| **Grand Total** | **[Total]** | **[Total]** | **[Total]** |\n\n"
            "Do not write Subtotal or Grand total outside the table. Put it INSIDE as the last row."
        ),
        expected_output="A 4-column markdown table showing Low, Medium, and High budget estimates.",
        agent=agents["budget"],
        context=[task_hotels, task_tickets],
    )

    return [task_research, task_weather, task_hotels, task_tickets, task_itinerary, task_budget]
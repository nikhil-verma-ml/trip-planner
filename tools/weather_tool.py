import os
import requests
from crewai.tools import tool


@tool("Weather Forecast Tool")
def get_weather_forecast(city: str) -> str:
    """
    Fetch the 5-day weather forecast for a given city using OpenWeatherMap API.
    Input: city name (e.g. 'Paris' or 'Mumbai').
    Returns temperature range, condition summary, and humidity for each day.
    """
    api_key = os.getenv("OPENWEATHER_API_KEY")
    if not api_key:
        return "Error: OPENWEATHER_API_KEY not set in .env"

    # Step 1 — Geocode city to lat/lon
    geo_url = "http://api.openweathermap.org/geo/1.0/direct"
    geo_params = {"q": city, "limit": 1, "appid": api_key}
    geo_resp = requests.get(geo_url, params=geo_params, timeout=10)

    if geo_resp.status_code != 200 or not geo_resp.json():
        return f"Error: Could not find city '{city}'. Check the city name."

    loc = geo_resp.json()[0]
    lat, lon = loc["lat"], loc["lon"]

    # Step 2 — Fetch 5-day forecast (3-hour intervals)
    forecast_url = "https://api.openweathermap.org/data/2.5/forecast"
    params = {
        "lat": lat,
        "lon": lon,
        "appid": api_key,
        "units": "metric",
        "cnt": 40,
    }
    resp = requests.get(forecast_url, params=params, timeout=10)

    if resp.status_code != 200:
        return f"Error fetching forecast: {resp.text}"

    data = resp.json()

    # Step 3 — Group by date and summarise
    daily: dict = {}
    for item in data["list"]:
        date = item["dt_txt"].split(" ")[0]
        if date not in daily:
            daily[date] = {"temps": [], "conditions": [], "humidity": []}
        daily[date]["temps"].append(item["main"]["temp"])
        daily[date]["conditions"].append(item["weather"][0]["description"])
        daily[date]["humidity"].append(item["main"]["humidity"])

    lines = [f"5-Day Weather Forecast for {city.title()}:\n"]
    for date, info in list(daily.items())[:5]:
        min_t = round(min(info["temps"]))
        max_t = round(max(info["temps"]))
        condition = max(set(info["conditions"]), key=info["conditions"].count).title()
        avg_hum = round(sum(info["humidity"]) / len(info["humidity"]))
        lines.append(
            f"  {date} → {condition} | {min_t}°C – {max_t}°C | Humidity: {avg_hum}%"
        )

    return "\n".join(lines)

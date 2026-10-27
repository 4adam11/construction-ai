"""Live forecast data from Open-Meteo (free, no API key)."""

from typing import Optional

import httpx

GEOCODE_URL = "https://geocoding-api.open-meteo.com/v1/search"
FORECAST_URL = "https://api.open-meteo.com/v1/forecast"

# WMO weather interpretation codes -> readable text
WMO = {
    0: "Clear sky", 1: "Mainly clear", 2: "Partly cloudy", 3: "Overcast",
    45: "Fog", 48: "Rime fog", 51: "Light drizzle", 53: "Drizzle", 55: "Dense drizzle",
    61: "Light rain", 63: "Rain", 65: "Heavy rain", 66: "Freezing rain", 67: "Heavy freezing rain",
    71: "Light snow", 73: "Snow", 75: "Heavy snow", 77: "Snow grains",
    80: "Light showers", 81: "Showers", 82: "Violent showers", 85: "Snow showers", 86: "Heavy snow showers",
    95: "Thunderstorm", 96: "Thunderstorm with hail", 99: "Severe thunderstorm with hail",
}


async def get_forecast(location: str, days: int = 7) -> Optional[dict]:
    """Return {"location": str, "days": [...]} or None if the location or service is unavailable."""
    try:
        async with httpx.AsyncClient(timeout=10) as client:
            geo = await client.get(GEOCODE_URL, params={"name": location, "count": 1})
            geo.raise_for_status()
            results = geo.json().get("results") or []
            if not results:
                return None
            place = results[0]
            fc = await client.get(FORECAST_URL, params={
                "latitude": place["latitude"],
                "longitude": place["longitude"],
                "daily": "weather_code,temperature_2m_max,temperature_2m_min,precipitation_sum,wind_speed_10m_max",
                "timezone": "auto",
                "forecast_days": days,
            })
            fc.raise_for_status()
            d = fc.json()["daily"]
    except (httpx.HTTPError, KeyError, ValueError):
        return None

    name = ", ".join(p for p in (place.get("name"), place.get("admin1"), place.get("country")) if p)
    return {
        "location": name,
        "days": [
            {
                "date": d["time"][i],
                "condition": WMO.get(d["weather_code"][i], "Unknown"),
                "temp_min_c": d["temperature_2m_min"][i],
                "temp_max_c": d["temperature_2m_max"][i],
                "precipitation_mm": d["precipitation_sum"][i],
                "wind_kmh": d["wind_speed_10m_max"][i],
            }
            for i in range(len(d["time"]))
        ],
    }

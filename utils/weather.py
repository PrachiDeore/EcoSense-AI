# utils/weather.py
import requests
from datetime import datetime, timezone

OWM_ONECALL = "https://api.openweathermap.org/data/2.5/onecall"

def fetch_hourly_weather(lat, lon, api_key):
    """Return hourly forecast list (next 48 hours) from OWM OneCall (JSON)."""
    params = {
        "lat": lat,
        "lon": lon,
        "exclude": "minutely,current,alerts",
        "units": "metric",
        "appid": api_key
    }
    r = requests.get(OWM_ONECALL, params=params, timeout=10)
    r.raise_for_status()
    data = r.json()
    return data["hourly"], data["timezone_offset"]

def compute_green_score(hourly_row, timezone_offset=0):
    """
    Simple green score: 1 - cloud_fraction, only if daytime (6–18h local time).
    """
    clouds = hourly_row.get("clouds", 0) / 100.0
    dt = datetime.fromtimestamp(hourly_row["dt"] + timezone_offset, tz=timezone.utc)
    hour = dt.hour
    is_day = 6 <= hour <= 18
    base = max(0.0, 1.0 - clouds)
    return base if is_day else 0.0

from __future__ import annotations
import os
from urllib.parse import urlencode
from typing import Dict, Any
from app.providers.http import client

OPEN_METEO = os.getenv("OPEN_METEO_API", "https://api.open-meteo.com")

async def forecast(lat: float, lng: float) -> Dict[str, Any]:
    params = {
        "latitude": lat,
        "longitude": lng,
        "daily": "temperature_2m_max,temperature_2m_min,precipitation_sum",
        "forecast_days": 3,
        "timezone": "auto",
    }
    url = f"{OPEN_METEO}/v1/forecast?{urlencode(params)}"
    async with client() as c:
        r = await c.get(url)
        r.raise_for_status()
        return r.json()

from __future__ import annotations
import os
from typing import Dict, Any
from urllib.parse import urlencode
from app.providers.http import client

OSRM_BASE = os.getenv("OSRM_BASE_URL", "https://router.project-osrm.org")

async def route_driving(o_lat: float, o_lng: float, d_lat: float, d_lng: float) -> Dict[str, Any]:
    coords = f"{o_lng},{o_lat};{d_lng},{d_lat}"
    params = {"overview":"full","geometries":"geojson","steps":"true","alternatives":"true"}
    url = f"{OSRM_BASE}/route/v1/driving/{coords}?{urlencode(params)}"
    async with client() as c:
        r = await c.get(url)
        r.raise_for_status()
        return r.json()

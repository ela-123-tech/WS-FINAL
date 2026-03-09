from __future__ import annotations
import os
from typing import List, Dict, Any
from app.providers.http import client
from app.utils import Throttle

_DEFAULT_ENDPOINTS = [
    "https://overpass-api.de/api/interpreter",
    "https://overpass.kumi.systems/api/interpreter",
    "https://overpass.nchc.org.tw/api/interpreter",
]
OVERPASS_ENDPOINTS = [
    e.strip() for e in os.getenv("OVERPASS_BASE_URLS", "").split(",") if e.strip()
] or _DEFAULT_ENDPOINTS
_throttle = Throttle(min_interval_s=1.0)

def _build_query(lat: float, lng: float, radius_m: int, kind: str) -> str:
    if kind == "food":
        return f"""[out:json][timeout:25];
( node(around:{radius_m},{lat},{lng})[amenity~"restaurant|cafe|fast_food"];
  way(around:{radius_m},{lat},{lng})[amenity~"restaurant|cafe|fast_food"];
  relation(around:{radius_m},{lat},{lng})[amenity~"restaurant|cafe|fast_food"]; );
out center tags 40;"""
    if kind == "hotel":
        return f"""[out:json][timeout:25];
( node(around:{radius_m},{lat},{lng})[tourism~"hotel|guest_house|hostel|motel"];
  way(around:{radius_m},{lat},{lng})[tourism~"hotel|guest_house|hostel|motel"];
  relation(around:{radius_m},{lat},{lng})[tourism~"hotel|guest_house|hostel|motel"]; );
out center tags 40;"""
    return f"""[out:json][timeout:25];
( node(around:{radius_m},{lat},{lng})[tourism="attraction"];
  way(around:{radius_m},{lat},{lng})[tourism="attraction"];
  relation(around:{radius_m},{lat},{lng})[tourism="attraction"]; );
out center tags 40;"""

async def _query_overpass(q: str) -> List[Dict[str, Any]]:
    last_error: Exception | None = None
    for base in OVERPASS_ENDPOINTS:
        try:
            async with client() as c:
                r = await c.post(base, content=q.encode("utf-8"), headers={"Content-Type":"text/plain; charset=utf-8"})
                r.raise_for_status()
                data = r.json()
            return data.get("elements", [])
        except Exception as e:
            last_error = e
            continue
    if last_error:
        raise last_error
    return []

async def search_pois(lat: float, lng: float, kind: str, radius_m: int = 20000) -> List[Dict[str, Any]]:
    await _throttle.wait()
    q = _build_query(lat, lng, radius_m, kind)
    return await _query_overpass(q)

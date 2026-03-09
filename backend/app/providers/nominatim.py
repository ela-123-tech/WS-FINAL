from __future__ import annotations
import os
from typing import Tuple
from urllib.parse import urlencode
from httpx import RequestError
from app.providers.http import client
from app.utils import Throttle

_throttle = Throttle(min_interval_s=1.0)
DEFAULT_NOMINATIM_BASE = "https://nominatim.openstreetmap.org"
NOMINATIM_BASE = os.getenv("NOMINATIM_BASE_URL", DEFAULT_NOMINATIM_BASE)
FALLBACK_PUBLIC = os.getenv("NOMINATIM_FALLBACK_PUBLIC", "true").lower() == "true"

async def geocode(place: str) -> Tuple[float, float, str]:
    await _throttle.wait()
    email = os.getenv("NOMINATIM_EMAIL")
    if not email and "nominatim.openstreetmap.org" in NOMINATIM_BASE:
        raise ValueError("NOMINATIM_EMAIL is required for public Nominatim")
    params = {"q": place, "format": "jsonv2", "limit": 1}
    if email:
        params["email"] = email

    async def _fetch(base: str) -> Tuple[float, float, str]:
        url = f"{base}/search.php?{urlencode(params)}"
        async with client() as c:
            r = await c.get(url)
            r.raise_for_status()
            data = r.json()
        if not data:
            raise ValueError(f"Could not geocode: {place}")
        item = data[0]
        return float(item["lat"]), float(item["lon"]), item.get("display_name", place)

    try:
        return await _fetch(NOMINATIM_BASE)
    except RequestError as exc:
        if FALLBACK_PUBLIC and NOMINATIM_BASE != DEFAULT_NOMINATIM_BASE:
            if not email:
                raise ValueError("NOMINATIM_EMAIL is required for public Nominatim") from exc
            return await _fetch(DEFAULT_NOMINATIM_BASE)
        raise

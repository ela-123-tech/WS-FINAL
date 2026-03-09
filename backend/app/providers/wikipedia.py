from __future__ import annotations
import os
from urllib.parse import urlencode, quote
from typing import Dict, Any, Optional
from app.providers.http import client

WIKI = os.getenv("WIKIPEDIA_API", "https://en.wikipedia.org")

async def _search_title(query: str) -> Optional[str]:
    params = {"action":"opensearch","search":query,"limit":1,"namespace":0,"format":"json"}
    url = f"{WIKI}/w/api.php?{urlencode(params)}"
    async with client() as c:
        r = await c.get(url)
        r.raise_for_status()
        data = r.json()
    titles = data[1] if len(data) > 1 else []
    return titles[0] if titles else None

async def summary(place: str) -> Dict[str, Any]:
    title = await _search_title(place) or place
    url = f"{WIKI}/api/rest_v1/page/summary/{quote(title)}"
    async with client() as c:
        r = await c.get(url)
        if r.status_code >= 400:
            return {"title": title, "extract": "", "ok": False}
        return r.json()

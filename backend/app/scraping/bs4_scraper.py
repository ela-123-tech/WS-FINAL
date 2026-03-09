from __future__ import annotations
import httpx
from bs4 import BeautifulSoup

async def fetch_text(url: str, max_chars: int = 4000) -> str:
    async with httpx.AsyncClient(timeout=25.0, follow_redirects=True, headers={"User-Agent":"TripGenFullstack/1.0"}) as c:
        r = await c.get(url)
        r.raise_for_status()
        html = r.text
    soup = BeautifulSoup(html, "lxml")
    for tag in soup(["script","style","noscript"]):
        tag.decompose()
    text = " ".join(soup.get_text(" ").split())
    return text[:max_chars]

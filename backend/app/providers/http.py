from __future__ import annotations
import os, httpx

DEFAULT_TIMEOUT = httpx.Timeout(20.0, connect=10.0)

def client() -> httpx.AsyncClient:
    email = os.getenv("NOMINATIM_EMAIL")
    user_agent = os.getenv("NOMINATIM_USER_AGENT", "TripGenFullstack/1.0")
    if email and "contact:" not in user_agent:
        user_agent = f"{user_agent} (contact: {email})"
    headers = {
        "User-Agent": user_agent,
        "Accept": "application/json",
    }
    if email:
        headers["From"] = email
    return httpx.AsyncClient(timeout=DEFAULT_TIMEOUT, headers=headers, follow_redirects=True)

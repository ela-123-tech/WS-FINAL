from __future__ import annotations
import asyncio
import csv
import io
import os
import zipfile
from dataclasses import dataclass
from typing import Dict, List, Tuple, Any

import httpx

GTFS_URL = os.getenv("GTFS_URL", "")

_gtfs_lock = asyncio.Lock()
_gtfs_data: dict | None = None

@dataclass
class Stop:
    stop_id: str
    name: str
    lat: float
    lng: float

def _parse_time_to_seconds(t: str) -> int | None:
    if not t:
        return None
    parts = t.strip().split(":")
    if len(parts) != 3:
        return None
    try:
        h, m, s = int(parts[0]), int(parts[1]), int(parts[2])
        return h * 3600 + m * 60 + s
    except ValueError:
        return None

def _seconds_to_iso_today(sec: int) -> str:
    # Use UTC date with provided seconds-of-day (wrap if > 24h).
    sec = sec % (24 * 3600)
    h = sec // 3600
    m = (sec % 3600) // 60
    s = sec % 60
    return f"{h:02d}:{m:02d}:{s:02d}Z"

def _haversine_km(lat1: float, lng1: float, lat2: float, lng2: float) -> float:
    from math import radians, sin, cos, asin, sqrt
    r = 6371.0
    phi1 = radians(lat1)
    phi2 = radians(lat2)
    dphi = radians(lat2 - lat1)
    dlambda = radians(lng2 - lng1)
    a = sin(dphi / 2) ** 2 + cos(phi1) * cos(phi2) * sin(dlambda / 2) ** 2
    return 2 * r * asin(sqrt(a))

async def _download_gtfs_zip(url: str) -> bytes:
    async with httpx.AsyncClient(timeout=60.0) as c:
        r = await c.get(url)
        r.raise_for_status()
        return r.content

def _read_csv_from_zip(z: zipfile.ZipFile, name: str) -> List[Dict[str, str]]:
    try:
        with z.open(name) as f:
            text = io.TextIOWrapper(f, encoding="utf-8", errors="replace")
            return list(csv.DictReader(text))
    except KeyError:
        return []

async def _load_gtfs() -> dict | None:
    if not GTFS_URL:
        return None
    blob = await _download_gtfs_zip(GTFS_URL)
    with zipfile.ZipFile(io.BytesIO(blob)) as z:
        stops_rows = _read_csv_from_zip(z, "stops.txt")
        stop_times_rows = _read_csv_from_zip(z, "stop_times.txt")
        trips_rows = _read_csv_from_zip(z, "trips.txt")
        routes_rows = _read_csv_from_zip(z, "routes.txt")

    stops: Dict[str, Stop] = {}
    for r in stops_rows:
        try:
            stops[r["stop_id"]] = Stop(
                stop_id=r["stop_id"],
                name=r.get("stop_name") or r["stop_id"],
                lat=float(r["stop_lat"]),
                lng=float(r["stop_lon"]),
            )
        except Exception:
            continue

    routes: Dict[str, dict] = {}
    for r in routes_rows:
        rid = r.get("route_id")
        if not rid:
            continue
        routes[rid] = {
            "short_name": r.get("route_short_name") or "",
            "long_name": r.get("route_long_name") or "",
        }

    trips: Dict[str, dict] = {}
    for r in trips_rows:
        tid = r.get("trip_id")
        if not tid:
            continue
        trips[tid] = {
            "route_id": r.get("route_id"),
            "headsign": r.get("trip_headsign") or "",
        }

    stop_times_by_trip: Dict[str, List[dict]] = {}
    for r in stop_times_rows:
        tid = r.get("trip_id")
        sid = r.get("stop_id")
        seq = r.get("stop_sequence")
        if not tid or not sid or not seq:
            continue
        try:
            seq_i = int(seq)
        except ValueError:
            continue
        stop_times_by_trip.setdefault(tid, []).append({
            "stop_id": sid,
            "seq": seq_i,
            "arrival": r.get("arrival_time") or "",
            "departure": r.get("departure_time") or "",
        })

    for tid, rows in stop_times_by_trip.items():
        rows.sort(key=lambda x: x["seq"])

    return {
        "stops": stops,
        "routes": routes,
        "trips": trips,
        "stop_times_by_trip": stop_times_by_trip,
    }

async def get_public_transit_options(
    origin_lat: float,
    origin_lng: float,
    dest_lat: float,
    dest_lng: float,
    radius_km: float = 2.0,
    max_results: int = 3,
) -> List[Dict[str, Any]]:
    global _gtfs_data
    if _gtfs_data is None:
        async with _gtfs_lock:
            if _gtfs_data is None:
                _gtfs_data = await _load_gtfs()
    if not _gtfs_data:
        return []

    stops: Dict[str, Stop] = _gtfs_data["stops"]
    routes: Dict[str, dict] = _gtfs_data["routes"]
    trips: Dict[str, dict] = _gtfs_data["trips"]
    stop_times_by_trip: Dict[str, List[dict]] = _gtfs_data["stop_times_by_trip"]

    origin_stops = {
        s.stop_id for s in stops.values()
        if _haversine_km(origin_lat, origin_lng, s.lat, s.lng) <= radius_km
    }
    dest_stops = {
        s.stop_id for s in stops.values()
        if _haversine_km(dest_lat, dest_lng, s.lat, s.lng) <= radius_km
    }
    if not origin_stops or not dest_stops:
        return []

    candidates: List[dict] = []
    for trip_id, rows in stop_times_by_trip.items():
        origin_idx = None
        dep_time = None
        for i, row in enumerate(rows):
            sid = row["stop_id"]
            if origin_idx is None and sid in origin_stops:
                origin_idx = i
                dep_time = row["departure"]
            elif origin_idx is not None and sid in dest_stops and i > origin_idx:
                arr_time = row["arrival"]
                dep_sec = _parse_time_to_seconds(dep_time or "")
                arr_sec = _parse_time_to_seconds(arr_time or "")
                if dep_sec is None or arr_sec is None or arr_sec <= dep_sec:
                    break
                duration_s = arr_sec - dep_sec
                trip_info = trips.get(trip_id, {})
                route_info = routes.get(trip_info.get("route_id"), {})
                title_bits = [route_info.get("short_name"), route_info.get("long_name")]
                title = "Public Transit"
                if any(title_bits):
                    title = "Public Transit — " + " ".join([t for t in title_bits if t]).strip()
                candidates.append({
                    "mode": "public_transit",
                    "operator": "Public Transit",
                    "title": title,
                    "departure_iso": _seconds_to_iso_today(dep_sec),
                    "arrival_iso": _seconds_to_iso_today(arr_sec),
                    "duration_s": duration_s,
                    "distance_m": None,
                    "price_inr": None,
                    "stops": (i - origin_idx - 1) if origin_idx is not None else None,
                    "booking_url": None,
                    "details": {
                        "trip_id": trip_id,
                        "route_id": trip_info.get("route_id"),
                        "headsign": trip_info.get("headsign"),
                    },
                })
                break

    candidates.sort(key=lambda x: x["duration_s"] or 10**9)
    return candidates[:max_results]

from __future__ import annotations
from typing import Dict, Any, List, Tuple
from datetime import datetime, timedelta
import math
import re
from urllib.parse import quote_plus
import asyncio

from sqlmodel import Session, select
from app import models
from app.providers.nominatim import geocode
from app.providers.osrm import route_driving
from app.providers.overpass import search_pois
from app.providers.open_meteo import forecast
from app.providers.wikipedia import summary as wiki_summary

def _osrm_to_route(route_json: Dict[str, Any]) -> Tuple[float, float, Dict[str, Any], List[Dict[str, Any]]]:
    routes = route_json.get("routes") or []
    if not routes:
        raise ValueError("No route found")
    r0 = routes[0]
    dist = float(r0.get("distance", 0))
    dur = float(r0.get("duration", 0))
    geom = r0.get("geometry") or {"type":"LineString","coordinates":[]}
    steps_out: List[Dict[str, Any]] = []
    for leg in (r0.get("legs") or []):
        for st in (leg.get("steps") or [])[:80]:
            man = st.get("maneuver") or {}
            steps_out.append({
                "name": st.get("name"),
                "distance": st.get("distance"),
                "duration": st.get("duration"),
                "instruction": man.get("instruction"),
                "type": man.get("type"),
                "modifier": man.get("modifier"),
                "location": man.get("location"),
            })
    return dist, dur, geom, steps_out

def _haversine_km(lat1: float, lng1: float, lat2: float, lng2: float) -> float:
    r = 6371.0
    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lng2 - lng1)
    a = math.sin(dphi / 2) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(dlambda / 2) ** 2
    return 2 * r * math.asin(math.sqrt(a))

def _fallback_route(o_lat: float, o_lng: float, d_lat: float, d_lng: float) -> Tuple[float, float, Dict[str, Any], List[Dict[str, Any]]]:
    km = _haversine_km(o_lat, o_lng, d_lat, d_lng)
    dist_m = km * 1000.0
    # Assume ~55 km/h average driving speed for rough duration.
    dur_s = int((km / 55.0) * 3600) if km > 0 else 0
    geom = {"type": "LineString", "coordinates": [[o_lng, o_lat], [d_lng, d_lat]]}
    return dist_m, dur_s, geom, []

def _slugify(text: str) -> str:
    text = text.lower()
    text = re.sub(r"[^a-z0-9]+", "-", text).strip("-")
    return text or "city"

def _city_name(text: str) -> str:
    if not text:
        return ""
    return text.split(",")[0].strip() or text

def _bus_booking_links(origin: str, destination: str) -> List[Dict[str, str]]:
    o_city = _city_name(origin)
    d_city = _city_name(destination)
    o_slug = _slugify(o_city)
    d_slug = _slugify(d_city)
    o_q = quote_plus(o_city)
    d_q = quote_plus(d_city)
    return [
        {
            "provider": "redBus",
            "label": "Book on redBus",
            "url": f"https://www.redbus.in/bus-tickets/{o_slug}-to-{d_slug}?fromCityName={o_q}&toCityName={d_q}",
        },
    ]


def _makemytrip_links() -> List[Dict[str, str]]:
    return [
        {
            "provider": "mmtCabs",
            "label": "Book on MakeMyTrip cabs",
            "url": "https://www.makemytrip.com/cabs/",
        },
        {
            "provider": "mmtCar",
            "label": "Book on MakeMyTrip car rental",
            "url": "https://www.makemytrip.com/car-rental/",
        },
    ]

def _make_transport_options(origin: str, destination: str, dist_m: float, dur_s: float) -> List[Dict[str, Any]]:
    km = dist_m / 1000.0
    opts: List[Dict[str, Any]] = []
    opts.append({
        "mode":"car","operator":None,"title":"Drive (Car)",
        "duration_s":int(dur_s),"distance_m":dist_m,"price_inr":round(km*6.5,0),"stops":0,
        "booking_url":None,"details":{"note":"Estimated fuel cost.","booking_links":_makemytrip_links()}
    })
    bike_kmh, walk_kmh = 16, 4.5
    opts.append({"mode":"bike","operator":None,"title":"Bike","duration_s":int((km/bike_kmh)*3600),"distance_m":dist_m,"price_inr":0,"stops":0,"booking_url":None,"details":{"note":"Estimated."}})
    opts.append({"mode":"walk","operator":None,"title":"Walk","duration_s":int((km/walk_kmh)*3600),"distance_m":dist_m,"price_inr":0,"stops":0,"booking_url":None,"details":{"note":"Estimated."}})

    now = datetime.utcnow().replace(microsecond=0)
    booking_links = _bus_booking_links(origin, destination)
    if booking_links:
        dep = now + timedelta(hours=2)
        arr = dep + timedelta(seconds=int(dur_s * 1.2))
        opts.append({
            "mode":"bus","operator":"",
            "title":f"Bus",
            "departure_iso":dep.isoformat()+"Z","arrival_iso":arr.isoformat()+"Z",
            "duration_s":int((arr-dep).total_seconds()),"distance_m":dist_m,
            "price_inr":float(250 + (km*1.2)),"stops":3,
            "booking_url": booking_links[0]["url"],
            "details":{
                "note":"Provider link only. Add schedule APIs for live data.",
                "booking_links": booking_links,
            }
        })
    return opts

def _overpass_to_pois(elements: List[Dict[str, Any]], kind: str) -> List[Dict[str, Any]]:
    out = []
    for el in elements:
        tags = el.get("tags") or {}
        name = tags.get("name")
        if not name:
            continue
        if el.get("type") == "node":
            lat = el.get("lat"); lng = el.get("lon")
        else:
            center = el.get("center") or {}
            lat = center.get("lat"); lng = center.get("lon")
        if lat is None or lng is None:
            continue
        addr_bits = []
        for k in ("addr:housenumber","addr:street","addr:suburb","addr:city","addr:state"):
            if tags.get(k): addr_bits.append(tags.get(k))
        addr = ", ".join(addr_bits) if addr_bits else None
        tag_list = []
        for k in ("amenity","tourism","cuisine"):
            if tags.get(k): tag_list.append(f"{k}:{tags.get(k)}")
        out.append({
            "kind":kind,"name":name,"lat":float(lat),"lng":float(lng),
            "address":addr,"rating":None,"price_level":tags.get("fee") or None,
            "tags":tag_list,
            "raw":{"tags":tags,"id":el.get("id"),"osm_type":el.get("type")}
        })
    return out[:40]

def _build_plans(transport_ids: List[int], hotel_ids: List[int], food_ids: List[int]) -> List[Dict[str, Any]]:
    def pick(lst): return lst[0] if lst else None
    plans = []
    plans.append({"name":"Cheapest","score":0.70,"transport_option_id":pick(transport_ids),"hotel_poi_id":pick(hotel_ids),"food_poi_id":pick(food_ids),
                  "summary":"Lowest estimated cost (rule-based).","costs":{"notes":"Estimates only."},
                  "timeline":[{"t":"Start","note":"Depart from origin"},{"t":"Arrive","note":"Reach destination"}]})
    plans.append({"name":"Fastest","score":0.90,"transport_option_id":pick(transport_ids),"hotel_poi_id":pick(hotel_ids),"food_poi_id":pick(food_ids),
                  "summary":"Fastest route estimate (rule-based).","costs":{"notes":"Traffic affects time."},
                  "timeline":[{"t":"Depart","note":"Begin trip"},{"t":"Arrive","note":"Destination"}]})
    plans.append({"name":"Balanced","score":0.85,"transport_option_id":pick(transport_ids),"hotel_poi_id":pick(hotel_ids),"food_poi_id":pick(food_ids),
                  "summary":"Balanced plan (cost + comfort).","costs":{"notes":"Balanced selection."},
                  "timeline":[{"t":"Depart","note":"Begin trip"},{"t":"Check-in","note":"Hotel"},{"t":"Dinner","note":"Restaurant"}]})
    comfort_transport = transport_ids[-1] if transport_ids else None
    plans.append({"name":"Comfort","score":0.80,"transport_option_id":comfort_transport,"hotel_poi_id":pick(hotel_ids),"food_poi_id":pick(food_ids),
                  "summary":"Comfort-oriented plan (rule-based).","costs":{"notes":"Replace placeholders for accuracy."},
                  "timeline":[{"t":"Depart","note":"Comfort travel"},{"t":"Arrive","note":"Relax"}]})
    return plans

async def build_trip(session: Session, origin: str, destination: str) -> models.Trip:
    o_lat, o_lng, o_disp = await geocode(origin)
    d_lat, d_lng, d_disp = await geocode(destination)

    trip = models.Trip(origin_text=origin, destination_text=destination,
                       origin_lat=o_lat, origin_lng=o_lng, dest_lat=d_lat, dest_lng=d_lng,
                       origin_display=o_disp, destination_display=d_disp, meta={})
    session.add(trip); session.commit(); session.refresh(trip)

    async def _safe(coro, default):
        try:
            return await coro
        except Exception:
            return default

    osrm_task = _safe(route_driving(o_lat, o_lng, d_lat, d_lng), None)
    hotels_task = _safe(search_pois(d_lat, d_lng, "hotel"), [])
    food_task = _safe(search_pois(d_lat, d_lng, "food"), [])
    attr_task = _safe(search_pois(d_lat, d_lng, "attraction"), [])
    weather_task = _safe(forecast(d_lat, d_lng), None)
    wiki_task = _safe(wiki_summary(destination), {})

    osrm_json, hotels_raw, food_raw, attr_raw, weather_json, wiki = await asyncio.gather(
        osrm_task, hotels_task, food_task, attr_task, weather_task, wiki_task
    )

    if osrm_json:
        dist, dur, geom, steps = _osrm_to_route(osrm_json)
    else:
        dist, dur, geom, steps = _fallback_route(o_lat, o_lng, d_lat, d_lng)
    session.add(models.Route(trip_id=trip.id, mode="driving", distance_m=dist, duration_s=dur, geometry_geojson=geom, steps=steps))

    for opt in _make_transport_options(origin, destination, dist, dur):
        session.add(models.TransportOption(trip_id=trip.id, **opt))

    # Remove public transit fallback; only car/bike/walk/bus options remain.

    for rec in _overpass_to_pois(hotels_raw, "hotel"):
        session.add(models.POI(trip_id=trip.id, source="osm_overpass", **rec))
    for rec in _overpass_to_pois(food_raw, "food"):
        session.add(models.POI(trip_id=trip.id, source="osm_overpass", **rec))
    for rec in _overpass_to_pois(attr_raw, "attraction"):
        session.add(models.POI(trip_id=trip.id, source="osm_overpass", **rec))

    trip.meta = {
        "weather": weather_json,
        "destination_summary": {
            "title": wiki.get("title"),
            "extract": wiki.get("extract"),
            "thumbnail": (wiki.get("thumbnail") or {}).get("source"),
            "page": wiki.get("content_urls", {}).get("desktop", {}).get("page"),
        },
        "providers": {"osrm":"public","overpass":"public","nominatim":"public"},
    }

    session.commit(); session.refresh(trip)

    transport_ids = [x for x in session.exec(select(models.TransportOption.id).where(models.TransportOption.trip_id==trip.id)).all()]
    hotel_ids = [x for x in session.exec(select(models.POI.id).where(models.POI.trip_id==trip.id, models.POI.kind=="hotel")).all()]
    food_ids  = [x for x in session.exec(select(models.POI.id).where(models.POI.trip_id==trip.id, models.POI.kind=="food")).all()]

    for plan in _build_plans(transport_ids, hotel_ids, food_ids):
        session.add(models.TripPlan(trip_id=trip.id, **plan))

    session.commit(); session.refresh(trip)
    return trip

def get_trip(session: Session, trip_id: int) -> models.Trip:
    trip = session.get(models.Trip, trip_id)
    if not trip:
        raise ValueError("Trip not found")
    _ = trip.route
    _ = trip.transport_options
    _ = trip.pois
    _ = trip.plans
    _ = trip.selection
    return trip

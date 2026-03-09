from __future__ import annotations
import os
from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select
from app.db import get_session
from app import models
from app.schemas import TripSearchRequest, TripOut, SelectRequest, ScrapePreviewRequest
from app.services.trip_builder import build_trip, get_trip
from app.excel.exporter import export_all, export_final

router = APIRouter()

def session_dep():
    with get_session() as s:
        yield s


@router.get("", include_in_schema=False)
def api_root():
    return {
        "ok": True,
        "message": "TripGen API is running. Use /trips/search to start.",
    }

@router.post("/trips/search", response_model=TripOut)
async def trips_search(payload: TripSearchRequest, session: Session = Depends(session_dep)):
    try:
        trip = await build_trip(session, payload.origin, payload.destination)
        trip = get_trip(session, trip.id)
        return _to_trip_out(trip)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/trips/{trip_id}", response_model=TripOut)
def trips_get(trip_id: int, session: Session = Depends(session_dep)):
    try:
        trip = get_trip(session, trip_id)
        return _to_trip_out(trip)
    except Exception as e:
        raise HTTPException(status_code=404, detail=str(e))

@router.post("/trips/{trip_id}/select")
def trips_select(trip_id: int, payload: SelectRequest, session: Session = Depends(session_dep)):
    trip = session.get(models.Trip, trip_id)
    if not trip:
        raise HTTPException(status_code=404, detail="Trip not found")

    t = session.get(models.TransportOption, payload.selected_transport_option_id)
    p = session.get(models.TripPlan, payload.selected_plan_id)
    if not t or t.trip_id != trip_id:
        raise HTTPException(status_code=400, detail="Invalid transport option")
    if not p or p.trip_id != trip_id:
        raise HTTPException(status_code=400, detail="Invalid plan")

    existing = session.exec(select(models.TripSelection).where(models.TripSelection.trip_id == trip_id)).first()
    if existing:
        existing.selected_transport_option_id = payload.selected_transport_option_id
        existing.selected_plan_id = payload.selected_plan_id
        session.add(existing); session.commit()
        return {"ok": True, "selection_id": existing.id}

    sel = models.TripSelection(trip_id=trip_id,
                              selected_transport_option_id=payload.selected_transport_option_id,
                              selected_plan_id=payload.selected_plan_id)
    session.add(sel); session.commit(); session.refresh(sel)
    return {"ok": True, "selection_id": sel.id}

@router.get("/trips/{trip_id}/export/all")
def trips_export_all(trip_id: int, session: Session = Depends(session_dep)):
    trip = get_trip(session, trip_id)
    filename = export_all(trip)
    session.add(models.ExportFile(trip_id=trip_id, kind="all", filename=filename))
    session.commit()
    return {"ok": True, "filename": filename, "download_url": f"/downloads/{filename}"}

@router.get("/trips/{trip_id}/export/final")
def trips_export_final(trip_id: int, session: Session = Depends(session_dep)):
    trip = get_trip(session, trip_id)
    sel = session.exec(select(models.TripSelection).where(models.TripSelection.trip_id == trip_id)).first()
    if not sel:
        raise HTTPException(status_code=400, detail="Select a transport option and plan first.")
    filename = export_final(trip, sel)
    session.add(models.ExportFile(trip_id=trip_id, kind="final", filename=filename))
    session.commit()
    return {"ok": True, "filename": filename, "download_url": f"/downloads/{filename}"}

@router.post("/scrape/preview")
async def scrape_preview(payload: ScrapePreviewRequest):
    enabled = os.getenv("SCRAPING_ENABLED", "false").lower() == "true"
    if not enabled:
        raise HTTPException(status_code=400, detail="Scraping is disabled. Set SCRAPING_ENABLED=true to enable.")
    if payload.mode == "bs4":
        from app.scraping.bs4_scraper import fetch_text
        text = await fetch_text(payload.url, payload.max_chars)
        return {"ok": True, "mode": "bs4", "text": text}
    from app.scraping.selenium_scraper import fetch_text
    text = fetch_text(payload.url, payload.max_chars)
    return {"ok": True, "mode": "selenium", "text": text}

def _to_trip_out(trip: models.Trip) -> TripOut:
    meta = trip.meta or {}
    route = None
    if trip.route:
        route = {"distance_m": trip.route.distance_m, "duration_s": trip.route.duration_s,
                 "geometry_geojson": trip.route.geometry_geojson, "steps": trip.route.steps or []}
    return TripOut(
        id=trip.id,
        origin_text=trip.origin_text,
        destination_text=trip.destination_text,
        origin_lat=trip.origin_lat,
        origin_lng=trip.origin_lng,
        dest_lat=trip.dest_lat,
        dest_lng=trip.dest_lng,
        origin_display=trip.origin_display,
        destination_display=trip.destination_display,
        route=route,
        transport_options=[{
            "id": t.id, "mode": t.mode, "operator": t.operator, "title": t.title,
            "departure_iso": t.departure_iso, "arrival_iso": t.arrival_iso,
            "duration_s": t.duration_s, "distance_m": t.distance_m, "price_inr": t.price_inr,
            "stops": t.stops, "booking_url": t.booking_url,
            "booking_links": (t.details or {}).get("booking_links", [])
        } for t in trip.transport_options],
        pois=[{
            "id": p.id, "kind": p.kind, "name": p.name, "lat": p.lat, "lng": p.lng,
            "address": p.address, "rating": p.rating, "price_level": p.price_level,
            "tags": p.tags or []
        } for p in trip.pois],
        plans=[{
            "id": pl.id, "name": pl.name, "score": pl.score, "transport_option_id": pl.transport_option_id,
            "hotel_poi_id": pl.hotel_poi_id, "food_poi_id": pl.food_poi_id, "summary": pl.summary,
            "costs": pl.costs or {}, "timeline": pl.timeline or []
        } for pl in trip.plans],
        weather=meta.get("weather"),
        destination_summary=meta.get("destination_summary"),
    )

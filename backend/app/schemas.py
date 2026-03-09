from __future__ import annotations
from pydantic import BaseModel, Field
from typing import Optional, Literal, List, Dict, Any

class TripSearchRequest(BaseModel):
    origin: str = Field(..., min_length=2)
    destination: str = Field(..., min_length=2)

class TransportOptionOut(BaseModel):
    id: int
    mode: str
    operator: Optional[str]
    title: str
    departure_iso: Optional[str]
    arrival_iso: Optional[str]
    duration_s: Optional[int]
    distance_m: Optional[float]
    price_inr: Optional[float]
    stops: Optional[int]
    booking_url: Optional[str]
    booking_links: List[Dict[str, Any]] = Field(default_factory=list)

class POIOut(BaseModel):
    id: int
    kind: str
    name: str
    lat: float
    lng: float
    address: Optional[str]
    rating: Optional[float]
    price_level: Optional[str]
    tags: List[str]

class RouteOut(BaseModel):
    distance_m: float
    duration_s: float
    geometry_geojson: Dict[str, Any]
    steps: List[Dict[str, Any]]

class TripPlanOut(BaseModel):
    id: int
    name: str
    score: float
    transport_option_id: Optional[int]
    hotel_poi_id: Optional[int]
    food_poi_id: Optional[int]
    summary: str
    costs: Dict[str, Any]
    timeline: List[Dict[str, Any]]

class TripOut(BaseModel):
    id: int
    origin_text: str
    destination_text: str
    origin_lat: float
    origin_lng: float
    dest_lat: float
    dest_lng: float
    origin_display: str
    destination_display: str
    route: Optional[RouteOut]
    transport_options: List[TransportOptionOut]
    pois: List[POIOut]
    plans: List[TripPlanOut]
    weather: Optional[Dict[str, Any]] = None
    destination_summary: Optional[Dict[str, Any]] = None

class SelectRequest(BaseModel):
    selected_transport_option_id: int
    selected_plan_id: int

class ScrapePreviewRequest(BaseModel):
    url: str
    mode: Literal["bs4", "selenium"] = "bs4"
    max_chars: int = 4000

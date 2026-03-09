from __future__ import annotations
from datetime import datetime
from typing import Optional, List
from sqlmodel import SQLModel, Field, Relationship
from sqlalchemy.orm import relationship
from sqlalchemy import Column, JSON

class Trip(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    origin_text: str
    destination_text: str

    origin_lat: float
    origin_lng: float
    dest_lat: float
    dest_lng: float

    origin_display: str
    destination_display: str

    created_at: datetime = Field(default_factory=datetime.utcnow)
    meta: dict = Field(default_factory=dict, sa_column=Column(JSON))

    route: Optional["Route"] = Relationship(
        sa_relationship=relationship("Route", back_populates="trip", uselist=False)
    )
    transport_options: List["TransportOption"] = Relationship(
        sa_relationship=relationship("TransportOption", back_populates="trip")
    )
    pois: List["POI"] = Relationship(
        sa_relationship=relationship("POI", back_populates="trip")
    )
    plans: List["TripPlan"] = Relationship(
        sa_relationship=relationship("TripPlan", back_populates="trip")
    )
    selection: Optional["TripSelection"] = Relationship(
        sa_relationship=relationship("TripSelection", back_populates="trip", uselist=False)
    )

class Route(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    trip_id: int = Field(foreign_key="trip.id", index=True)
    mode: str = "driving"
    distance_m: float
    duration_s: float
    geometry_geojson: dict = Field(sa_column=Column(JSON))
    steps: list = Field(default_factory=list, sa_column=Column(JSON))
    trip: "Trip" = Relationship(
        sa_relationship=relationship("Trip", back_populates="route")
    )

class TransportOption(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    trip_id: int = Field(foreign_key="trip.id", index=True)
    mode: str
    operator: Optional[str] = None
    title: str
    departure_iso: Optional[str] = None
    arrival_iso: Optional[str] = None
    duration_s: Optional[int] = None
    distance_m: Optional[float] = None
    price_inr: Optional[float] = None
    stops: Optional[int] = None
    booking_url: Optional[str] = None
    details: dict = Field(default_factory=dict, sa_column=Column(JSON))
    trip: "Trip" = Relationship(
        sa_relationship=relationship("Trip", back_populates="transport_options")
    )

class POI(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    trip_id: int = Field(foreign_key="trip.id", index=True)
    kind: str
    name: str
    lat: float
    lng: float
    address: Optional[str] = None
    rating: Optional[float] = None
    price_level: Optional[str] = None
    tags: list = Field(default_factory=list, sa_column=Column(JSON))
    source: str = "osm_overpass"
    raw: dict = Field(default_factory=dict, sa_column=Column(JSON))
    trip: "Trip" = Relationship(
        sa_relationship=relationship("Trip", back_populates="pois")
    )

class TripPlan(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    trip_id: int = Field(foreign_key="trip.id", index=True)
    name: str
    score: float = 0.0
    transport_option_id: Optional[int] = None
    hotel_poi_id: Optional[int] = None
    food_poi_id: Optional[int] = None
    summary: str = ""
    costs: dict = Field(default_factory=dict, sa_column=Column(JSON))
    timeline: list = Field(default_factory=list, sa_column=Column(JSON))
    trip: "Trip" = Relationship(
        sa_relationship=relationship("Trip", back_populates="plans")
    )

class TripSelection(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    trip_id: int = Field(foreign_key="trip.id", index=True, unique=True)
    selected_transport_option_id: int
    selected_plan_id: int
    created_at: datetime = Field(default_factory=datetime.utcnow)
    trip: "Trip" = Relationship(
        sa_relationship=relationship("Trip", back_populates="selection")
    )

class ExportFile(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    trip_id: int = Field(foreign_key="trip.id", index=True)
    kind: str
    filename: str
    created_at: datetime = Field(default_factory=datetime.utcnow)

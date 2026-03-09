from __future__ import annotations
import os
from sqlmodel import SQLModel, create_engine, Session

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./app.db")
engine = create_engine(DATABASE_URL, echo=False, pool_pre_ping=True)

def init_db() -> None:
    from app import models  # noqa: F401
    SQLModel.metadata.create_all(engine)

def get_session() -> Session:
    return Session(engine)

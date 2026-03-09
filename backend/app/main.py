from __future__ import annotations
import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from dotenv import load_dotenv
from app.db import init_db
from app.api.routes import router as api_router

load_dotenv()

app = FastAPI(title="TripGen API", version="1.0.0")

cors_origins = [o.strip() for o in os.getenv("CORS_ORIGINS", "http://localhost:5173").split(",") if o.strip()]
app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("startup")
def on_startup() -> None:
    init_db()

app.include_router(api_router, prefix="/api")

@app.get("/health")
def health():
    return {"ok": True}

@app.get("/downloads/{filename}")
def download_file(filename: str):
    base = os.path.abspath(os.path.join(os.path.dirname(__file__), "exports"))
    path = os.path.abspath(os.path.join(base, filename))
    if not path.startswith(base):
        return {"error": "invalid path"}
    if not os.path.exists(path):
        return {"error": "not found"}
    return FileResponse(path, filename=filename)

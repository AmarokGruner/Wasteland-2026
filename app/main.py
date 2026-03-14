from fastapi import FastAPI, Request
from pydantic import BaseModel
from typing import List, Optional, Any
import sqlite3
import os
import uvicorn
import json
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import RedirectResponse, FileResponse
import datetime
from apscheduler.schedulers.background import BackgroundScheduler
from contextlib import asynccontextmanager

DB_PATH = "verbrannte_zone.db"

def get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def row_to_dict(row):
    return dict(row)

# --- Scheduler Setup ---
scheduler = BackgroundScheduler()

def scheduled_tick():
    from app.tick_logic import run_tick
    db = None
    try:
        from app.models import SessionLocal
        db = SessionLocal()
        run_tick(db)
    finally:
        if db:
            db.close()

# Start scheduler on startup
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Pass 1-hour interval for game ticks
    scheduler.add_job(scheduled_tick, 'interval', hours=1, id='server_tick_job')
    scheduler.start()
    yield
    scheduler.shutdown()

app = FastAPI(title="Verbrannte Zone API", lifespan=lifespan)

app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

# --- Import API Router ---
from app.api import api_router
app.include_router(api_router)

# --- Static file serving ---
@app.get("/")
async def read_root():
    return FileResponse("index.html")

@app.get("/admin.html")
async def serve_admin():
    return FileResponse("admin.html")

@app.get("/login.html")
async def serve_login():
    return FileResponse("login.html")

@app.get("/index.html")
async def serve_index():
    return FileResponse("index.html")

# Mount JS, CSS and Terrain directories
app.mount("/js", StaticFiles(directory="js"), name="js")
app.mount("/css", StaticFiles(directory="css"), name="css")
app.mount("/terrains", StaticFiles(directory="terrains"), name="terrains")

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
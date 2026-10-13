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
import logging

# Configure logging for the application
logging.basicConfig(
    level=logging.INFO,  # Production: INFO; change to DEBUG for development
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),  # Console output (uvicorn logs)
    ]
)

# Optional: File handler for persistent logs
log_file = os.path.join(os.path.dirname(__file__), '..', 'logs', 'wasteland.log')
os.makedirs(os.path.join(os.path.dirname(__file__), '..', 'logs'), exist_ok=True)
try:
    file_handler = logging.FileHandler(log_file)
    file_handler.setLevel(logging.DEBUG)  # Always log DEBUG to file
    file_format = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    file_handler.setFormatter(file_format)
    logging.getLogger().addHandler(file_handler)
except Exception:
    pass  # File logging is optional; continue if it fails

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

# Error Tracking Middleware
from app.middleware.error_tracking import ErrorTrackingMiddleware
app.add_middleware(ErrorTrackingMiddleware)

# Rate Limiting Middleware
from app.middleware.rate_limiting import setup_rate_limiter
setup_rate_limiter(app)

# --- Import API Router ---
from app.api import api_router
app.include_router(api_router)

# --- Static file serving ---
@app.get("/")
async def read_root():
    return FileResponse("index.html")

@app.get("/admin.html")
async def serve_admin():
    response = FileResponse("admin.html")
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Pragma"] = "no-cache"
    response.headers["Expires"] = "0"
    return response

@app.get("/login.html")
async def serve_login():
    return FileResponse("login.html")

@app.get("/help.html")
async def serve_help():
    return FileResponse("help.html")

@app.get("/index.html")
async def serve_index():
    return FileResponse("index.html")

# Mount JS, CSS and Terrain directories
app.mount("/js", StaticFiles(directory="js"), name="js")
app.mount("/css", StaticFiles(directory="css"), name="css")
app.mount("/terrains", StaticFiles(directory="terrains"), name="terrains")

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
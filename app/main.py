from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List, Optional
import sqlite3
import os
import uvicorn
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import RedirectResponse

DB_PATH = "data.db"

def get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(
        """CREATE TABLE IF NOT EXISTS buildings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL
        )"""
    )
    cur.execute(
        """CREATE TABLE IF NOT EXISTS resources (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            type TEXT,
            production_value INTEGER,
            land_transport_cost INTEGER,
            water_transport_cost INTEGER,
            air_transport_cost INTEGER,
            description TEXT,
            consumption_per_1000_per_day REAL
        )"""
    )
    cur.execute(
        """CREATE TABLE IF NOT EXISTS resource_consumes_buildings (
            resource_id INTEGER,
            building_id INTEGER,
            FOREIGN KEY(resource_id) REFERENCES resources(id),
            FOREIGN KEY(building_id) REFERENCES buildings(id)
        )"""
    )
    cur.execute(
        """CREATE TABLE IF NOT EXISTS resource_produces_buildings (
            resource_id INTEGER,
            building_id INTEGER,
            FOREIGN KEY(resource_id) REFERENCES resources(id),
            FOREIGN KEY(building_id) REFERENCES buildings(id)
        )"""
    )
    conn.commit()
    conn.close()

init_db()

class ResourceBase(BaseModel):
    name: str
    type: Optional[str] = None
    production_value: Optional[int] = None
    land_transport_cost: Optional[int] = None
    water_transport_cost: Optional[int] = None
    air_transport_cost: Optional[int] = None
    description: Optional[str] = None
    consumption_per_1000_per_day: Optional[float] = None

class ResourceCreate(ResourceBase):
    consumes_buildings: Optional[List[int]] = []
    produces_buildings: Optional[List[int]] = []

class ResourceUpdate(ResourceBase):
    consumes_buildings: Optional[List[int]] = []
    produces_buildings: Optional[List[int]] = []

class ResourceOut(ResourceBase):
    id: int
    consumes_buildings: List[int] = []
    produces_buildings: List[int] = []

app = FastAPI(title="Resource Editor API")

# Allow local frontend testing
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

# Serve simple admin UI for resources (static files under /admin)
app.mount("/admin", StaticFiles(directory="admin"), name="admin")

# German alias route to help existing admin UI users
@app.get("/admin/ressourcen")
async def redirect_ressourcen():
    return RedirectResponse(url="/admin/resources.html")

@app.get("/admin/ressourcen/{path:path}")
async def redirect_ressourcen_path(path: str):
    return RedirectResponse(url="/admin/resources.html")

def to_resource_dict(row):
    return {
        "id": row["id"],
        "name": row["name"],
        "type": row["type"],
        "production_value": row["production_value"],
        "land_transport_cost": row["land_transport_cost"],
        "water_transport_cost": row["water_transport_cost"],
        "air_transport_cost": row["air_transport_cost"],
        "description": row["description"],
        "consumption_per_1000_per_day": row["consumption_per_1000_per_day"],
    }

@app.get("/api/resources/fields")
def get_resource_fields():
    # Static, reliable field schema for testing. Can be expanded later from DB.
    fields = [
        {"name": "name", "type": "string", "label": "Name", "required": True},
        {"name": "type", "type": "enum", "label": "Typ", "options": ["Baurohstoff", "Nahrung", "Genussgut", "Andere"]},
        {"name": "production_value", "type": "number", "label": "Produktionswert"},
        {"name": "land_transport_cost", "type": "number", "label": "Platzverbrauch Landtransport"},
        {"name": "water_transport_cost", "type": "number", "label": "Platzverbrauch Wassertransport"},
        {"name": "air_transport_cost", "type": "number", "label": "Platzverbrauch Lufttransport"},
        {"name": "consumes_buildings", "type": "relation", "label": "Folgende Gebäude verbrauchen", "relation": {"target": "buildings", "cardinality": "many"}},
        {"name": "produces_buildings", "type": "relation", "label": "Folgende Gebäude produzieren", "relation": {"target": "buildings", "cardinality": "many"}},
        {"name": "description", "type": "text", "label": "Beschreibung"},
        {"name": "consumption_per_1000_per_day", "type": "number", "label": "Verbrauch pro 1000 Personen/Tag"},
    ]
    return fields

def derive_fields_from_external_db():
    # Obsolete in this patch; kept only for compatibility, but not used by the static endpoint.
    return []

@app.get("/api/buildings")
def list_buildings():
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT id, name FROM buildings ORDER BY name")
    buildings = [{"id": r["id"], "name": r["name"]} for r in cur.fetchall()]
    conn.close()
    return buildings

@app.get("/api/resources")
def list_resources():
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT * FROM resources ORDER BY id")
    rows = cur.fetchall()
    res = []
    for r in rows:
        cur.execute("SELECT building_id FROM resource_consumes_buildings WHERE resource_id=?", (r["id"],))
        consumes = [x[0] for x in cur.fetchall()]
        cur.execute("SELECT building_id FROM resource_produces_buildings WHERE resource_id=?", (r["id"],))
        produces = [x[0] for x in cur.fetchall()]
        res.append({
            "id": r["id"],
            "name": r["name"],
            "type": r["type"],
            "production_value": r["production_value"],
            "land_transport_cost": r["land_transport_cost"],
            "water_transport_cost": r["water_transport_cost"],
            "air_transport_cost": r["air_transport_cost"],
            "description": r["description"],
            "consumption_per_1000_per_day": r["consumption_per_1000_per_day"],
            "consumes_buildings": consumes,
            "produces_buildings": produces,
        })
    conn.close()
    return res

@app.get("/api/resources/{resource_id}")
def get_resource(resource_id: int):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT * FROM resources WHERE id=?", (resource_id,))
    row = cur.fetchone()
    if not row:
        raise HTTPException(status_code=404, detail="Resource not found")
    cur.execute("SELECT building_id FROM resource_consumes_buildings WHERE resource_id=?", (resource_id,))
    consumes = [x[0] for x in cur.fetchall()]
    cur.execute("SELECT building_id FROM resource_produces_buildings WHERE resource_id=?", (resource_id,))
    produces = [x[0] for x in cur.fetchall()]
    conn.close()
    return {
        "id": row["id"],
        "name": row["name"],
        "type": row["type"],
        "production_value": row["production_value"],
        "land_transport_cost": row["land_transport_cost"],
        "water_transport_cost": row["water_transport_cost"],
        "air_transport_cost": row["air_transport_cost"],
        "description": row["description"],
        "consumption_per_1000_per_day": row["consumption_per_1000_per_day"],
        "consumes_buildings": consumes,
        "produces_buildings": produces,
    }

@app.post("/api/resources")
def create_resource(res: ResourceCreate):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO resources(name, type, production_value, land_transport_cost, water_transport_cost, air_transport_cost, description, consumption_per_1000_per_day)
        VALUES (?,?,?,?,?,?,?,?)
    """, (res.name, res.type, res.production_value, res.land_transport_cost, res.water_transport_cost, res.air_transport_cost, res.description, res.consumption_per_1000_per_day))
    if cur.lastrowid is None:
        raise HTTPException(status_code=500, detail="Resource creation failed: no ID returned")
    resource_id = int(cur.lastrowid)
    for bid in (res.consumes_buildings or []):
        cur.execute("INSERT INTO resource_consumes_buildings(resource_id, building_id) VALUES (?, ?)", (resource_id, bid))
    for bid in (res.produces_buildings or []):
        cur.execute("INSERT INTO resource_produces_buildings(resource_id, building_id) VALUES (?, ?)", (resource_id, bid))
    conn.commit()
    conn.close()
    return get_resource(resource_id)

@app.put("/api/resources/{resource_id}")
def update_resource(resource_id: int, res: ResourceUpdate):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        UPDATE resources SET
            name=?, type=?, production_value=?, land_transport_cost=?, water_transport_cost=?, air_transport_cost=?, description=?, consumption_per_1000_per_day=?
        WHERE id=?
    """, (res.name, res.type, res.production_value, res.land_transport_cost, res.water_transport_cost, res.air_transport_cost, res.description, res.consumption_per_1000_per_day, resource_id))
    cur.execute("DELETE FROM resource_consumes_buildings WHERE resource_id=?", (resource_id,))
    cur.execute("DELETE FROM resource_produces_buildings WHERE resource_id=?", (resource_id,))
    for bid in (res.consumes_buildings or []):
        cur.execute("INSERT INTO resource_consumes_buildings(resource_id, building_id) VALUES (?, ?)", (resource_id, bid))
    for bid in (res.produces_buildings or []):
        cur.execute("INSERT INTO resource_produces_buildings(resource_id, building_id) VALUES (?, ?)", (resource_id, bid))
    conn.commit()
    conn.close()
    return get_resource(resource_id)

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)

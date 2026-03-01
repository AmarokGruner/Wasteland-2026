#!/usr/bin/env python3
"""main.py v2.1.0 – Verbrannte Zone Backend
Neu: Benutzer-Authentifizierung und Admin-Dashboard"""
from fastapi import FastAPI, HTTPException, Depends, status
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, List
import sqlite3, json, os, math, hashlib
from datetime import datetime, timedelta
import secrets

DB_PATH = "verbrannte_zone.db"
SECRET_KEY = "vz-secret-key-change-in-production"

# JWT helper functions
def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

def create_token(user_id, username, role):
    """Create a simple token (for demo - use JWT in production)."""
    data = f"{user_id}:{username}:{role}:{datetime.now().timestamp()}"
    return hashlib.sha256(data.encode()).hexdigest()[:32]

def verify_token(token):
    """Verify token and return user info."""
    conn = get_db()
    cur = conn.cursor()
    import json
    cur.execute("SELECT id, username, role, player_id FROM users WHERE token = ?", (token,))
    user = cur.fetchone()
    conn.close()
    if user:
        return {"id": user[0], "username": user[1], "role": user[2], "player_id": user[3]}
    return None

def get_current_user(token: str = None):
    """Dependency to get current user from token."""
    if not token:
        return None
    return verify_token(token)

# Auth Models
class LoginRequest(BaseModel):
    username: str
    password: str

class LoginResponse(BaseModel):
    token: str
    user_id: int
    username: str
    role: str
    player_id: Optional[int] = None

ROAD_COSTS     = {1:50,  2:100, 3:200, 4:400}
CROSSING_COSTS = {1:100, 2:200, 3:400, 4:800}
BUILDING_COSTS = {"building_mine":500,"building_factory":1000,"building_bunker":0,
                  "building_powerplant":1500,"building_refinery":1202,
                  "Feldweg":50,"Feldwegkreuzung":80,
                  "Kiesweg":100,"Kieskreuzung":150}
HANDELSKARREN_ID       = 1   # Ressource-ID
HANDELSKARREN_KAPAZITÄT = 100  # Platz pro Karren

for _d in ["css","js","terrains"]:
    os.makedirs(_d, exist_ok=True)

# ─── DB ──────────────────────────────────────────────────────────────────────
def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn

def init_db():
    conn = get_db(); cur = conn.cursor()

    # Stamm-Tabellen
    cur.execute("""CREATE TABLE IF NOT EXISTS players (
        id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT NOT NULL DEFAULT 'Spieler',
        iron INTEGER DEFAULT 1000, steel INTEGER DEFAULT 500, fuel INTEGER DEFAULT 200,
        last_turn_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)""")

    # Migration: last_turn_timestamp hinzufügen falls er fehlt
    try:
        cur.execute("ALTER TABLE players ADD COLUMN last_turn_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP")
    except: pass

    cur.execute("""CREATE TABLE IF NOT EXISTS roads (
        id INTEGER PRIMARY KEY AUTOINCREMENT, player_id INTEGER NOT NULL,
        world_x INTEGER NOT NULL, world_y INTEGER NOT NULL,
        grid_x INTEGER NOT NULL, grid_y INTEGER NOT NULL,
        road_type TEXT NOT NULL DEFAULT 'road', level INTEGER DEFAULT 1,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (player_id) REFERENCES players(id))""")

    cur.execute("""CREATE TABLE IF NOT EXISTS buildings (
        id INTEGER PRIMARY KEY AUTOINCREMENT, player_id INTEGER NOT NULL,
        world_x INTEGER NOT NULL, world_y INTEGER NOT NULL,
        building_x INTEGER NOT NULL, building_y INTEGER NOT NULL,
        building_type TEXT NOT NULL, created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        UNIQUE(player_id,world_x,world_y,building_x,building_y),
        FOREIGN KEY (player_id) REFERENCES players(id))""")

    cur.execute("""CREATE TABLE IF NOT EXISTS gebaeude_typen (
        id INTEGER PRIMARY KEY, name TEXT NOT NULL,
        symbol_emoji TEXT DEFAULT '', symbol_url TEXT DEFAULT '', bild_url TEXT DEFAULT '',
        kategorie TEXT DEFAULT '', bautyp TEXT DEFAULT 'Land',
        baubar INTEGER DEFAULT 1, ausbaubar INTEGER DEFAULT 0,
        unique_gebaeude INTEGER DEFAULT 0, nur_kueste INTEGER DEFAULT 0, ist_feld INTEGER DEFAULT 0,
        tech_level INTEGER DEFAULT 0, baukosten_mips INTEGER DEFAULT 0,
        ausbaukosten_mips INTEGER DEFAULT 0, energiebedarf INTEGER DEFAULT 0,
        arbeiter INTEGER DEFAULT 0, zusatzarbeiter_pro_stufe INTEGER DEFAULT 0,
        wohnraum INTEGER DEFAULT 0, zusatzwohnraum_pro_stufe INTEGER DEFAULT 0,
        lagerkapazitaet INTEGER DEFAULT 0, beschreibung TEXT DEFAULT '',
        rohstoffbedarf_bau TEXT DEFAULT '[]', rohstoffgrundbedarf_ausbau TEXT DEFAULT '[]',
        rohstoffverbrauch TEXT DEFAULT '[]', produktion TEXT DEFAULT '[]',
        terrain_effektivitaet TEXT DEFAULT '{}', vorkommen_effektivitaet TEXT DEFAULT '{}',
        spezial_eigenschaften TEXT DEFAULT '{}', schlachtfeld TEXT DEFAULT '{}',
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)""")

    cur.execute("""CREATE TABLE IF NOT EXISTS provinz_feldtypen (
        id TEXT PRIMARY KEY, name TEXT NOT NULL, beschreibung TEXT DEFAULT '',
        groesse_px INTEGER DEFAULT 30, ist_baubar INTEGER DEFAULT 1,
        bautypen TEXT DEFAULT '[]', farbe_leer TEXT DEFAULT '#444',
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)""")

    cur.execute("""CREATE TABLE IF NOT EXISTS ressourcen (
        id INTEGER PRIMARY KEY, name TEXT NOT NULL UNIQUE, typ TEXT NOT NULL,
        wert INTEGER DEFAULT 0, verbrauch INTEGER DEFAULT 0, platzbedarf INTEGER DEFAULT 1,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)""")

    cur.execute("""CREATE TABLE IF NOT EXISTS vorkommen (
        id INTEGER PRIMARY KEY, name TEXT NOT NULL UNIQUE,
        typ TEXT NOT NULL, tech INTEGER DEFAULT 0, suchkosten INTEGER DEFAULT 0,
        beschreibung TEXT DEFAULT '', findwahrscheinlichkeit TEXT DEFAULT '{}',
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)""")

    # NEU: Provinz-Besitz
    cur.execute("""CREATE TABLE IF NOT EXISTS provinzen (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        player_id INTEGER NOT NULL,
        world_x INTEGER NOT NULL,
        world_y INTEGER NOT NULL,
        name TEXT DEFAULT '',
        terrain TEXT DEFAULT 'Grasland',
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        UNIQUE(world_x, world_y),
        FOREIGN KEY (player_id) REFERENCES players(id))""")

    # Migration: terrain Spalte hinzufügen falls sie fehlt
    try:
        cur.execute("ALTER TABLE provinzen ADD COLUMN terrain TEXT DEFAULT 'Grasland'")
    except:
        pass

    # NEU: Ressourcen-Lager pro Provinz
    cur.execute("""CREATE TABLE IF NOT EXISTS provinz_lager (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        provinz_id INTEGER NOT NULL,
        ressource_id INTEGER NOT NULL,
        menge INTEGER NOT NULL DEFAULT 0,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        UNIQUE(provinz_id, ressource_id),
        FOREIGN KEY (provinz_id) REFERENCES provinzen(id),
        FOREIGN KEY (ressource_id) REFERENCES ressourcen(id))""")

    # NEU: Handelskarren-Transport-Log
    cur.execute("""CREATE TABLE IF NOT EXISTS handelskarren_transport (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        player_id INTEGER NOT NULL,
        von_provinz_id INTEGER NOT NULL,
        nach_provinz_id INTEGER NOT NULL,
        ressource_id INTEGER NOT NULL,
        menge INTEGER NOT NULL,
        karren_benoetigt INTEGER NOT NULL DEFAULT 1,
        status TEXT NOT NULL DEFAULT 'angekommen',
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        angekommen_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (player_id) REFERENCES players(id),
        FOREIGN KEY (von_provinz_id) REFERENCES provinzen(id),
        FOREIGN KEY (nach_provinz_id) REFERENCES provinzen(id),
        FOREIGN KEY (ressource_id) REFERENCES ressourcen(id))""")

    # --- Migrationen ---
    # gebaeude (level hinzufügen)
    try: cur.execute("ALTER TABLE buildings ADD COLUMN level INTEGER DEFAULT 1")
    except: pass

    # Migrationen (gebaeude_typen)
    for col, defn in [
        ("vorkommen_effektivitaet","TEXT DEFAULT '{}'"),
        ("ausbaukosten_mips","INTEGER DEFAULT 0"),
        ("rohstoffgrundbedarf_ausbau","TEXT DEFAULT '[]'"),
        ("zusatzarbeiter_pro_stufe","INTEGER DEFAULT 0"),
        ("zusatzwohnraum_pro_stufe","INTEGER DEFAULT 0"),
    ]:
        try: cur.execute(f"ALTER TABLE gebaeude_typen ADD COLUMN {col} {defn}")
        except: pass

    # Migrationen (vorkommen)
    for col, defn in [
        ("beschreibung","TEXT DEFAULT ''"),
        ("findwahrscheinlichkeit","TEXT DEFAULT '{}'"),
    ]:
        try: cur.execute(f"ALTER TABLE vorkommen ADD COLUMN {col} {defn}")
        except: pass

    # Migrationen (handelskarren_transport – nachträglich fehlende Spalten)
    for col, defn in [
        ("distanz","INTEGER DEFAULT 0"),
        ("delay_minuten","INTEGER DEFAULT 0"),
        ("ankunft_geplant","TIMESTAMP DEFAULT CURRENT_TIMESTAMP"),
    ]:
        try: cur.execute(f"ALTER TABLE handelskarren_transport ADD COLUMN {col} {defn}")
        except: pass

    # Default-Spieler + Provinz-Feldtypen
    cur.execute("INSERT OR IGNORE INTO players (id,name) VALUES (1,'Spieler 1')")
    for ft in [
        ("gebaeude","Gebäudefeld","Landfeld",30,1,'["Land"]',"#5a7a3a"),
        ("stadt","Stadtfeld","Stadtfeld",30,1,'["Stadt"]',"#6a6a8a"),
        ("stadtausbau","Stadtausbau","Provinzausbau",30,1,'["Stadtausbau"]',"#4a4a7a"),
        ("weg","Wegfeld","Wegfeld",10,1,'["Weg"]',"#8b7355"),
        ("kreuzung","Kreuzungsfeld","Kreuzung",10,1,'["Wegkreuzung"]',"#7a6345"),
        ("vorgabe","Vorgabefeld","Vorgabe",30,0,'["Vorgabe"]',"#3a3a5a"),
    ]:
        cur.execute("INSERT OR IGNORE INTO provinz_feldtypen (id,name,beschreibung,groesse_px,ist_baubar,bautypen,farbe_leer) VALUES (?,?,?,?,?,?,?)",ft)

    conn.commit(); conn.close()

init_db()

# ─── FastAPI ──────────────────────────────────────────────────────────────────
app = FastAPI(title="Verbrannte Zone API", version="2.1.0")

# ─── Auth Endpoints ─────────────────────────────────────────────────────────
@app.post("/auth/login", response_model=LoginResponse)
async def login(credentials: LoginRequest):
    """Authenticate user and return token."""
    conn = get_db()
    cur = conn.cursor()
    
    pw_hash = hash_password(credentials.password)
    cur.execute("""
        SELECT id, username, role, player_id 
        FROM users 
        WHERE username = ? AND password_hash = ?
    """, (credentials.username, pw_hash))
    
    user = cur.fetchone()
    if not user:
        conn.close()
        raise HTTPException(401, "Invalid username or password")
    
    # Create token
    token = create_token(user[0], user[1], user[2])
    cur.execute("UPDATE users SET token = ? WHERE id = ?", (token, user[0]))
    conn.commit()
    conn.close()
    
    return LoginResponse(
        token=token,
        user_id=user[0],
        username=user[1],
        role=user[2],
        player_id=user[3]
    )

@app.post("/auth/logout")
async def logout(request: dict):
    """Logout user by clearing token."""
    token = request.get("token") if isinstance(request, dict) else None
    if token:
        conn = get_db()
        cur = conn.cursor()
        cur.execute("UPDATE users SET token = NULL WHERE token = ?", (token,))
        conn.commit()
        conn.close()
    return {"message": "Logged out successfully"}

@app.get("/auth/me")
async def get_me(token: Optional[str] = None):
    """Get current user info."""
    if not token:
        raise HTTPException(401, "Not authenticated")
    
    user = verify_token(token)
    if not user:
        raise HTTPException(401, "Invalid token")
    
    return user

# ─── Admin Endpoints ───────────────────────────────────────────────────────
def require_admin(token: str = None):
    """Dependency that requires admin role."""
    if not token:
        raise HTTPException(401, "Not authenticated")
    user = verify_token(token)
    if not user or user["role"] != "admin":
        raise HTTPException(403, "Admin access required")
    return user

@app.get("/admin/users")
async def list_users(token: str = None, admin=Depends(require_admin)):
    """List all users (admin only)."""
    conn = get_db()
    cur = conn.cursor()
    cur.execute("""
        SELECT u.id, u.username, u.role, u.player_id, u.created_at, p.name as player_name
        FROM users u
        LEFT JOIN players p ON u.player_id = p.id
        ORDER BY u.id
    """)
    users = [dict(row) for row in cur.fetchall()]
    conn.close()
    return users

@app.post("/admin/users")
async def create_user(
    username: str, 
    password: str, 
    role: str = "player",
    player_id: Optional[int] = None,
    token: str = None,
    admin=Depends(require_admin)
):
    """Create new user (admin only)."""
    conn = get_db()
    cur = conn.cursor()
    
    pw_hash = hash_password(password)
    try:
        cur.execute("""
            INSERT INTO users (username, password_hash, role, player_id)
            VALUES (?, ?, ?, ?)
        """, (username, pw_hash, role, player_id))
        conn.commit()
        user_id = cur.lastrowid
        conn.close()
        return {"message": f"User {username} created", "user_id": user_id}
    except sqlite3.IntegrityError:
        conn.close()
        raise HTTPException(400, "Username already exists")

@app.get("/admin/buildings")
async def list_building_types(token: str = None, admin=Depends(require_admin)):
    """List all building types (admin only)."""
    conn = get_db()
    cur = conn.cursor()
    cur.execute("SELECT * FROM gebaeude_typen ORDER BY name")
    buildings = [dict(row) for row in cur.fetchall()]
    conn.close()
    return buildings

@app.put("/admin/buildings/{building_id}")
async def update_building_type(
    building_id: int,
    name: str = None,
    kategorie: str = None,
    baukosten_mips: int = None,
    arbeiter: int = None,
    wohnraum: int = None,
    lagerkapazitaet: int = None,
    produktion: str = None,
    rohstoffverbrauch: str = None,
    terrain_effektivitaet: str = None,
    token: str = None,
    admin=Depends(require_admin)
):
    """Update building type (admin only)."""
    conn = get_db()
    cur = conn.cursor()
    
    # Build dynamic update
    updates = []
    values = []
    if name is not None:
        updates.append("name = ?")
        values.append(name)
    if kategorie is not None:
        updates.append("kategorie = ?")
        values.append(kategorie)
    if baukosten_mips is not None:
        updates.append("baukosten_mips = ?")
        values.append(baukosten_mips)
    if arbeiter is not None:
        updates.append("arbeiter = ?")
        values.append(arbeiter)
    if wohnraum is not None:
        updates.append("wohnraum = ?")
        values.append(wohnraum)
    if lagerkapazitaet is not None:
        updates.append("lagerkapazitaet = ?")
        values.append(lagerkapazitaet)
    if produktion is not None:
        prod = json.loads(produktion) if isinstance(produktion, str) else produktion
        updates.append("produktion = ?")
        values.append(json.dumps(prod))
    if rohstoffverbrauch is not None:
        cons = json.loads(rohstoffverbrauch) if isinstance(rohstoffverbrauch, str) else rohstoffverbrauch
        updates.append("rohstoffverbrauch = ?")
        values.append(json.dumps(cons))
    if terrain_effektivitaet is not None:
        terr = json.loads(terrain_effektivitaet) if isinstance(terrain_effektivitaet, str) else terrain_effektivitaet
        updates.append("terrain_effektivitaet = ?")
        values.append(json.dumps(terr))
    
    if not updates:
        raise HTTPException(400, "No fields to update")
    
    values.append(building_id)
    cur.execute(f"UPDATE gebaeude_typen SET {', '.join(updates)} WHERE id = ?", values)
    conn.commit()
    conn.close()
    return {"message": "Building type updated"}

@app.post("/admin/buildings")
async def create_building_type(
    name: str,
    kategorie: str = "Sonstiges",
    baukosten_mips: int = 0,
    arbeiter: int = 0,
    wohnraum: int = 0,
    lagerkapazitaet: int = 0,
    produktion: str = "[]",
    rohstoffverbrauch: str = "[]",
    terrain_effektivitaet: str = "{}",
    token: str = None,
    admin=Depends(require_admin)
):
    """Create new building type (admin only)."""
    conn = get_db()
    cur = conn.cursor()
    
    try:
        import json
        # Validate and normalize JSON fields from UI
        prod_data = json.loads(produktion) if isinstance(produktion, str) else produktion
        cons_data = json.loads(rohstoffverbrauch) if isinstance(rohstoffverbrauch, str) else rohstoffverbrauch
        terrain_data = json.loads(terrain_effektivitaet) if isinstance(terrain_effektivitaet, str) else terrain_effektivitaet
        if not isinstance(prod_data, list):
            raise ValueError('Produktion must be a list')
        for item in prod_data:
            if not isinstance(item, dict) or 'ressource' not in item or 'menge' not in item:
                raise ValueError('Produktion-Elemente müssen Objekte mit keys "ressource" und "menge" sein')
        if not isinstance(cons_data, list):
            raise ValueError('Verbrauch muss eine Liste sein')
        for item in cons_data:
            if not isinstance(item, dict) or 'ressource' not in item or 'menge' not in item:
                raise ValueError('Verbrauch-Elemente müssen Objekte mit keys "ressource" und "menge" sein')
        if not isinstance(terrain_data, dict):
            raise ValueError('Terrain-Effektivität muss ein Objekt sein')
        for k, v in terrain_data.items():
            if not isinstance(k, str) or not isinstance(v, list):
                raise ValueError('Terrain-Effektivität muss eine Map von String zu Liste sein')
        prod_json = json.dumps(prod_data)
        cons_json = json.dumps(cons_data)
        terrain_json = json.dumps(terrain_data)
        cur.execute("""
            INSERT INTO gebaeude_typen (name, kategorie, baukosten_mips, arbeiter, wohnraum, lagerkapazitaet, produktion, rohstoffverbrauch, terrain_effektivitaet)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (name, kategorie, baukosten_mips, arbeiter, wohnraum, lagerkapazitaet, prod_json, cons_json, terrain_json))
        conn.commit()
        building_id = cur.lastrowid
        conn.close()
        return {"message": f"Building type {name} created", "building_id": building_id}
    except sqlite3.IntegrityError:
        conn.close()
        raise HTTPException(400, "Building type already exists")

@app.delete("/admin/buildings/{building_id}")
async def delete_building_type(
    building_id: int,
    token: str = None,
    admin=Depends(require_admin)
):
    """Delete building type (admin only)."""
    conn = get_db()
    cur = conn.cursor()
    
    cur.execute("DELETE FROM gebaeude_typen WHERE id = ?", (building_id,))
    if cur.rowcount == 0:
        conn.close()
        raise HTTPException(404, "Building type not found")
    
    conn.commit()
    conn.close()
    return {"message": "Building type deleted"}

# ─── Admin: Rohstoffe (ressourcen) ────────────────────────────────────────────────
@app.get("/admin/ressourcen")
async def list_ressourcen(token: str = None, admin=Depends(require_admin)):
    """List all resources (admin only)."""
    conn = get_db()
    cur = conn.cursor()
    cur.execute("SELECT * FROM ressourcen ORDER BY typ, name")
    rows = cur.fetchall()
    conn.close()
    return [dict(r) for r in rows]

@app.post("/admin/ressourcen")
async def create_ressource(
    name: str,
    typ: str = "Sonstiges",
    wert: int = 0,
    verbrauch: int = 0,
    platzbedarf: int = 0,
    token: str = None,
    admin=Depends(require_admin)
):
    """Create new resource (admin only)."""
    conn = get_db()
    cur = conn.cursor()
    try:
        cur.execute("""
            INSERT INTO ressourcen (name, typ, wert, verbrauch, platzbedarf)
            VALUES (?, ?, ?, ?, ?)
        """, (name, typ, wert, verbrauch, platzbedarf))
        conn.commit()
        ressource_id = cur.lastrowid
        conn.close()
        return {"message": f"Ressource {name} created", "ressource_id": ressource_id}
    except sqlite3.IntegrityError:
        conn.close()
        raise HTTPException(400, "Ressource already exists")

@app.put("/admin/ressourcen/{ressource_id}")
async def update_ressource(
    ressource_id: int,
    name: str = None,
    typ: str = None,
    wert: int = None,
    verbrauch: int = None,
    platzbedarf: int = None,
    token: str = None,
    admin=Depends(require_admin)
):
    """Update resource (admin only)."""
    conn = get_db()
    cur = conn.cursor()
    updates = []
    values = []
    if name is not None:
        updates.append("name = ?")
        values.append(name)
    if typ is not None:
        updates.append("typ = ?")
        values.append(typ)
    if wert is not None:
        updates.append("wert = ?")
        values.append(wert)
    if verbrauch is not None:
        updates.append("verbrauch = ?")
        values.append(verbrauch)
    if platzbedarf is not None:
        updates.append("platzbedarf = ?")
        values.append(platzbedarf)
    if not updates:
        raise HTTPException(400, "No fields to update")
    values.append(ressource_id)
    cur.execute(f"UPDATE ressourcen SET {', '.join(updates)} WHERE id = ?", values)
    conn.commit()
    conn.close()
    return {"message": "Ressource updated"}

@app.delete("/admin/ressourcen/{ressource_id}")
async def delete_ressource(
    ressource_id: int,
    token: str = None,
    admin=Depends(require_admin)
):
    """Delete resource (admin only)."""
    conn = get_db()
    cur = conn.cursor()
    cur.execute("DELETE FROM ressourcen WHERE id = ?", (ressource_id,))
    if cur.rowcount == 0:
        conn.close()
        raise HTTPException(404, "Ressource not found")
    conn.commit()
    conn.close()
    return {"message": "Ressource deleted"}

# ─── Admin: Vorkommen ─────────────────────────────────────────────────────────────
@app.get("/admin/vorkommen")
async def list_vorkommen(token: str = None, admin=Depends(require_admin)):
    """List all occurrences (admin only)."""
    conn = get_db()
    cur = conn.cursor()
    cur.execute("SELECT * FROM vorkommen ORDER BY typ, name")
    rows = cur.fetchall()
    conn.close()
    return [dict(r) for r in rows]

@app.post("/admin/vorkommen")
async def create_vorkommen(
    name: str,
    typ: str = "Sonstiges",
    tech: int = 0,
    suchkosten: int = 0,
    beschreibung: str = "",
    findwahrscheinlichkeit: str = "{}",
    token: str = None,
    admin=Depends(require_admin)
):
    """Create new occurrence (admin only)."""
    import json
    conn = get_db()
    cur = conn.cursor()
    try:
        find_data = json.loads(findwahrscheinlichkeit) if isinstance(findwahrscheinlichkeit, str) else findwahrscheinlichkeit
        cur.execute("""
            INSERT INTO vorkommen (name, typ, tech, suchkosten, beschreibung, findwahrscheinlichkeit)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (name, typ, tech, suchkosten, beschreibung, json.dumps(find_data)))
        conn.commit()
        vorkommen_id = cur.lastrowid
        conn.close()
        return {"message": f"Vorkommen {name} created", "vorkommen_id": vorkommen_id}
    except sqlite3.IntegrityError:
        conn.close()
        raise HTTPException(400, "Vorkommen already exists")

@app.put("/admin/vorkommen/{vorkommen_id}")
async def update_vorkommen(
    vorkommen_id: int,
    name: str = None,
    typ: str = None,
    tech: int = None,
    suchkosten: int = None,
    beschreibung: str = None,
    findwahrscheinlichkeit: str = None,
    token: str = None,
    admin=Depends(require_admin)
):
    """Update occurrence (admin only)."""
    import json
    conn = get_db()
    cur = conn.cursor()
    updates = []
    values = []
    if name is not None:
        updates.append("name = ?")
        values.append(name)
    if typ is not None:
        updates.append("typ = ?")
        values.append(typ)
    if tech is not None:
        updates.append("tech = ?")
        values.append(tech)
    if suchkosten is not None:
        updates.append("suchkosten = ?")
        values.append(suchkosten)
    if beschreibung is not None:
        updates.append("beschreibung = ?")
        values.append(beschreibung)
    if findwahrscheinlichkeit is not None:
        find_data = json.loads(findwahrscheinlichkeit) if isinstance(findwahrscheinlichkeit, str) else findwahrscheinlichkeit
        updates.append("findwahrscheinlichkeit = ?")
        values.append(json.dumps(find_data))
    if not updates:
        raise HTTPException(400, "No fields to update")
    values.append(vorkommen_id)
    cur.execute(f"UPDATE vorkommen SET {', '.join(updates)} WHERE id = ?", values)
    conn.commit()
    conn.close()
    return {"message": "Vorkommen updated"}

@app.delete("/admin/vorkommen/{vorkommen_id}")
async def delete_vorkommen(
    vorkommen_id: int,
    token: str = None,
    admin=Depends(require_admin)
):
    """Delete occurrence (admin only)."""
    conn = get_db()
    cur = conn.cursor()
    cur.execute("DELETE FROM vorkommen WHERE id = ?", (vorkommen_id,))
    if cur.rowcount == 0:
        conn.close()
        raise HTTPException(404, "Vorkommen not found")
    conn.commit()
    conn.close()
    return {"message": "Vorkommen deleted"}

# ─── Admin: Gebäude-Felder (provinz_feldtypen) ───────────────────────────────────────
@app.get("/admin/gebaeude_felder")
async def list_gebaeude_felder(token: str = None, admin=Depends(require_admin)):
    """List all building field types (admin only)."""
    conn = get_db()
    cur = conn.cursor()
    cur.execute("SELECT * FROM provinz_feldtypen ORDER BY name")
    rows = cur.fetchall()
    conn.close()
    return [dict(r) for r in rows]

@app.post("/admin/gebaeude_felder")
async def create_gebaeude_feld(
    id: str,
    name: str,
    beschreibung: str = "",
    groesse_px: int = 30,
    ist_baubar: int = 1,
    bautypen: str = "[]",
    farbe_leer: str = "#000000",
    token: str = None,
    admin=Depends(require_admin)
):
    """Create new building field type (admin only)."""
    import json
    conn = get_db()
    cur = conn.cursor()
    try:
        bautypen_data = json.loads(bautypen) if isinstance(bautypen, str) else bautypen
        cur.execute("""
            INSERT INTO provinz_feldtypen (id, name, beschreibung, groesse_px, ist_baubar, bautypen, farbe_leer)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (id, name, beschreibung, groesse_px, ist_baubar, json.dumps(bautypen_data), farbe_leer))
        conn.commit()
        conn.close()
        return {"message": f"Gebaeude-Feld {name} created"}
    except sqlite3.IntegrityError:
        conn.close()
        raise HTTPException(400, "Gebaeude-Feld already exists")

@app.put("/admin/gebaeude_felder/{feld_id}")
async def update_gebaeude_feld(
    feld_id: str,
    name: str = None,
    beschreibung: str = None,
    groesse_px: int = None,
    ist_baubar: int = None,
    bautypen: str = None,
    farbe_leer: str = None,
    token: str = None,
    admin=Depends(require_admin)
):
    """Update building field type (admin only)."""
    import json
    conn = get_db()
    cur = conn.cursor()
    updates = []
    values = []
    if name is not None:
        updates.append("name = ?")
        values.append(name)
    if beschreibung is not None:
        updates.append("beschreibung = ?")
        values.append(beschreibung)
    if groesse_px is not None:
        updates.append("groesse_px = ?")
        values.append(groesse_px)
    if ist_baubar is not None:
        updates.append("ist_baubar = ?")
        values.append(ist_baubar)
    if bautypen is not None:
        bautypen_data = json.loads(bautypen) if isinstance(bautypen, str) else bautypen
        updates.append("bautypen = ?")
        values.append(json.dumps(bautypen_data))
    if farbe_leer is not None:
        updates.append("farbe_leer = ?")
        values.append(farbe_leer)
    if not updates:
        raise HTTPException(400, "No fields to update")
    values.append(feld_id)
    cur.execute(f"UPDATE provinz_feldtypen SET {', '.join(updates)} WHERE id = ?", values)
    conn.commit()
    conn.close()
    return {"message": "Gebaeude-Feld updated"}

@app.delete("/admin/gebaeude_felder/{feld_id}")
async def delete_gebaeude_feld(
    feld_id: str,
    token: str = None,
    admin=Depends(require_admin)
):
    """Delete building field type (admin only)."""
    conn = get_db()
    cur = conn.cursor()
    cur.execute("DELETE FROM provinz_feldtypen WHERE id = ?", (feld_id,))
    if cur.rowcount == 0:
        conn.close()
        raise HTTPException(404, "Gebaeude-Feld not found")
    conn.commit()
    conn.close()
    return {"message": "Gebaeude-Feld deleted"}

# ─── Admin: Welt-Terrain (world_terrain) ───────────────────────────────────────────
@app.get("/admin/terrain")
async def list_terrain(token: str = None, admin=Depends(require_admin)):
    """List all world terrain types (admin only)."""
    conn = get_db()
    cur = conn.cursor()
    cur.execute("SELECT * FROM world_terrain ORDER BY name")
    rows = cur.fetchall()
    conn.close()
    return [dict(r) for r in rows]

@app.post("/admin/terrain")
async def create_terrain(
    id: str,
    name: str,
    farbe: str = "#000000",
    icon: str = "",
    beschreibung: str = "",
    spielbar: int = 1,
    ressourcen: str = "[]",
    erlaubte_gebaeude: str = "[]",
    token: str = None,
    admin=Depends(require_admin)
):
    """Create new world terrain type (admin only)."""
    import json
    conn = get_db()
    cur = conn.cursor()
    try:
        ressourcen_data = json.loads(ressourcen) if isinstance(ressourcen, str) else ressourcen
        gebaeude_data = json.loads(erlaubte_gebaeude) if isinstance(erlaubte_gebaeude, str) else erlaubte_gebaeude
        cur.execute("""
            INSERT INTO world_terrain (id, name, farbe, icon, beschreibung, spielbar, ressourcen, erlaubte_gebaeude)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (id, name, farbe, icon, beschreibung, spielbar, json.dumps(ressourcen_data), json.dumps(gebaeude_data)))
        conn.commit()
        conn.close()
        return {"message": f"Terrain {name} created"}
    except sqlite3.IntegrityError:
        conn.close()
        raise HTTPException(400, "Terrain already exists")

@app.put("/admin/terrain/{terrain_id}")
async def update_terrain(
    terrain_id: str,
    name: str = None,
    farbe: str = None,
    icon: str = None,
    beschreibung: str = None,
    spielbar: int = None,
    ressourcen: str = None,
    erlaubte_gebaeude: str = None,
    token: str = None,
    admin=Depends(require_admin)
):
    """Update world terrain type (admin only)."""
    import json
    conn = get_db()
    cur = conn.cursor()
    updates = []
    values = []
    if name is not None:
        updates.append("name = ?")
        values.append(name)
    if farbe is not None:
        updates.append("farbe = ?")
        values.append(farbe)
    if icon is not None:
        updates.append("icon = ?")
        values.append(icon)
    if beschreibung is not None:
        updates.append("beschreibung = ?")
        values.append(beschreibung)
    if spielbar is not None:
        updates.append("spielbar = ?")
        values.append(spielbar)
    if ressourcen is not None:
        ressourcen_data = json.loads(ressourcen) if isinstance(ressourcen, str) else ressourcen
        updates.append("ressourcen = ?")
        values.append(json.dumps(ressourcen_data))
    if erlaubte_gebaeude is not None:
        gebaeude_data = json.loads(erlaubte_gebaeude) if isinstance(erlaubte_gebaeude, str) else erlaubte_gebaeude
        updates.append("erlaubte_gebaeude = ?")
        values.append(json.dumps(gebaeude_data))
    if not updates:
        raise HTTPException(400, "No fields to update")
    values.append(terrain_id)
    cur.execute(f"UPDATE world_terrain SET {', '.join(updates)} WHERE id = ?", values)
    conn.commit()
    conn.close()
    return {"message": "Terrain updated"}

@app.delete("/admin/terrain/{terrain_id}")
async def delete_terrain(
    terrain_id: str,
    token: str = None,
    admin=Depends(require_admin)
):
    """Delete world terrain type (admin only)."""
    conn = get_db()
    cur = conn.cursor()
    cur.execute("DELETE FROM world_terrain WHERE id = ?", (terrain_id,))
    if cur.rowcount == 0:
        conn.close()
        raise HTTPException(404, "Terrain not found")
    conn.commit()
    conn.close()
    return {"message": "Terrain deleted"}

# ─── Admin: Artikel ────────────────────────────────────────────────────────────────
@app.get("/admin/artikel")
async def list_artikel(token: str = None, admin=Depends(require_admin)):
    """List all items (admin only)."""
    conn = get_db()
    cur = conn.cursor()
    cur.execute("SELECT * FROM artikel ORDER BY kategorie, name")
    rows = cur.fetchall()
    conn.close()
    return [dict(r) for r in rows]

@app.post("/admin/artikel")
async def create_artikel(
    name: str,
    beschreibung: str = "",
    kategorie: str = "Sonstiges",
    preis_mips: int = 0,
    preis_muenzen: int = 0,
    gewicht: int = 0,
    haltbarkeit: int = -1,
    token: str = None,
    admin=Depends(require_admin)
):
    """Create new item (admin only)."""
    conn = get_db()
    cur = conn.cursor()
    try:
        cur.execute("""
            INSERT INTO artikel (name, beschreibung, kategorie, preis_mips, preis_muenzen, gewicht, haltbarkeit)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (name, beschreibung, kategorie, preis_mips, preis_muenzen, gewicht, haltbarkeit))
        conn.commit()
        artikel_id = cur.lastrowid
        conn.close()
        return {"message": f"Artikel {name} created", "artikel_id": artikel_id}
    except sqlite3.IntegrityError:
        conn.close()
        raise HTTPException(400, "Artikel already exists")

@app.put("/admin/artikel/{artikel_id}")
async def update_artikel(
    artikel_id: int,
    name: str = None,
    beschreibung: str = None,
    kategorie: str = None,
    preis_mips: int = None,
    preis_muenzen: int = None,
    gewicht: int = None,
    haltbarkeit: int = None,
    token: str = None,
    admin=Depends(require_admin)
):
    """Update item (admin only)."""
    conn = get_db()
    cur = conn.cursor()
    updates = []
    values = []
    if name is not None:
        updates.append("name = ?")
        values.append(name)
    if beschreibung is not None:
        updates.append("beschreibung = ?")
        values.append(beschreibung)
    if kategorie is not None:
        updates.append("kategorie = ?")
        values.append(kategorie)
    if preis_mips is not None:
        updates.append("preis_mips = ?")
        values.append(preis_mips)
    if preis_muenzen is not None:
        updates.append("preis_muenzen = ?")
        values.append(preis_muenzen)
    if gewicht is not None:
        updates.append("gewicht = ?")
        values.append(gewicht)
    if haltbarkeit is not None:
        updates.append("haltbarkeit = ?")
        values.append(haltbarkeit)
    if not updates:
        raise HTTPException(400, "No fields to update")
    values.append(artikel_id)
    cur.execute(f"UPDATE artikel SET {', '.join(updates)} WHERE id = ?", values)
    conn.commit()
    conn.close()
    return {"message": "Artikel updated"}

@app.delete("/admin/artikel/{artikel_id}")
async def delete_artikel(
    artikel_id: int,
    token: str = None,
    admin=Depends(require_admin)
):
    """Delete item (admin only)."""
    conn = get_db()
    cur = conn.cursor()
    cur.execute("DELETE FROM artikel WHERE id = ?", (artikel_id,))
    if cur.rowcount == 0:
        conn.close()
        raise HTTPException(404, "Artikel not found")
    conn.commit()
    conn.close()
    return {"message": "Artikel deleted"}

# ─── Admin: Einheiten-Typen ────────────────────────────────────────────────────────
@app.get("/admin/einheiten")
async def list_einheiten_typen(token: str = None, admin=Depends(require_admin)):
    """List all unit types (admin only)."""
    conn = get_db()
    cur = conn.cursor()
    cur.execute("SELECT * FROM einheiten_typen ORDER BY kategorie, name")
    rows = cur.fetchall()
    conn.close()
    return [dict(r) for r in rows]

@app.post("/admin/einheiten")
async def create_einheiten_typ(
    name: str,
    kategorie: str = "Infanterie",
    kosten_mips: int = 0,
    kosten_muenzen: int = 0,
    bevoelkerung_count: int = 1,
    bewaffnung: str = "",
    transport_kapazitaet: int = 0,
    geschwindigkeit: int = 1,
    token: str = None,
    admin=Depends(require_admin)
):
    """Create new unit type (admin only)."""
    conn = get_db()
    cur = conn.cursor()
    try:
        cur.execute("""
            INSERT INTO einheiten_typen (name, kategorie, kosten_mips, kosten_muenzen, bevoelkerung_count, bewaffnung, transport_kapazitaet, geschwindigkeit)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (name, kategorie, kosten_mips, kosten_muenzen, bevoelkerung_count, bewaffnung, transport_kapazitaet, geschwindigkeit))
        conn.commit()
        einheiten_id = cur.lastrowid
        conn.close()
        return {"message": f"Einheiten-Typ {name} created", "einheiten_id": einheiten_id}
    except sqlite3.IntegrityError:
        conn.close()
        raise HTTPException(400, "Einheiten-Typ already exists")

@app.put("/admin/einheiten/{einheiten_id}")
async def update_einheiten_typ(
    einheiten_id: int,
    name: str = None,
    kategorie: str = None,
    kosten_mips: int = None,
    kosten_muenzen: int = None,
    bevoelkerung_count: int = None,
    bewaffnung: str = None,
    transport_kapazitaet: int = None,
    geschwindigkeit: int = None,
    token: str = None,
    admin=Depends(require_admin)
):
    """Update unit type (admin only)."""
    conn = get_db()
    cur = conn.cursor()
    updates = []
    values = []
    if name is not None:
        updates.append("name = ?")
        values.append(name)
    if kategorie is not None:
        updates.append("kategorie = ?")
        values.append(kategorie)
    if kosten_mips is not None:
        updates.append("kosten_mips = ?")
        values.append(kosten_mips)
    if kosten_muenzen is not None:
        updates.append("kosten_muenzen = ?")
        values.append(kosten_muenzen)
    if bevoelkerung_count is not None:
        updates.append("bevoelkerung_count = ?")
        values.append(bevoelkerung_count)
    if bewaffnung is not None:
        updates.append("bewaffnung = ?")
        values.append(bewaffnung)
    if transport_kapazitaet is not None:
        updates.append("transport_kapazitaet = ?")
        values.append(transport_kapazitaet)
    if geschwindigkeit is not None:
        updates.append("geschwindigkeit = ?")
        values.append(geschwindigkeit)
    if not updates:
        raise HTTPException(400, "No fields to update")
    values.append(einheiten_id)
    cur.execute(f"UPDATE einheiten_typen SET {', '.join(updates)} WHERE id = ?", values)
    conn.commit()
    conn.close()
    return {"message": "Einheiten-Typ updated"}

@app.delete("/admin/einheiten/{einheiten_id}")
async def delete_einheiten_typ(
    einheiten_id: int,
    token: str = None,
    admin=Depends(require_admin)
):
    """Delete unit type (admin only)."""
    conn = get_db()
    cur = conn.cursor()
    cur.execute("DELETE FROM einheiten_typen WHERE id = ?", (einheiten_id,))
    if cur.rowcount == 0:
        conn.close()
        raise HTTPException(404, "Einheiten-Typ not found")
    conn.commit()
    conn.close()
    return {"message": "Einheiten-Typ deleted"}

# ─── Admin: Lebewesen ─────────────────────────────────────────────────────────────
@app.get("/admin/lebewesen")
async def list_lebewesen(token: str = None, admin=Depends(require_admin)):
    """List all creatures (admin only)."""
    conn = get_db()
    cur = conn.cursor()
    cur.execute("SELECT * FROM lebewesen ORDER BY typ, name")
    rows = cur.fetchall()
    conn.close()
    return [dict(r) for r in rows]

@app.post("/admin/lebewesen")
async def create_lebewesen(
    name: str,
    typ: str = "Neutral",
    staerke: int = 10,
    gesundheit: int = 100,
    bevoelkerung_kosten: int = 0,
    beschreibung: str = "",
    token: str = None,
    admin=Depends(require_admin)
):
    """Create new creature (admin only)."""
    conn = get_db()
    cur = conn.cursor()
    try:
        cur.execute("""
            INSERT INTO lebewesen (name, typ, staerke, gesundheit, bevoelkerung_kosten, beschreibung)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (name, typ, staerke, gesundheit, bevoelkerung_kosten, beschreibung))
        conn.commit()
        lebewesen_id = cur.lastrowid
        conn.close()
        return {"message": f"Lebewesen {name} created", "lebewesen_id": lebewesen_id}
    except sqlite3.IntegrityError:
        conn.close()
        raise HTTPException(400, "Lebewesen already exists")

@app.put("/admin/lebewesen/{lebewesen_id}")
async def update_lebewesen(
    lebewesen_id: int,
    name: str = None,
    typ: str = None,
    staerke: int = None,
    gesundheit: int = None,
    bevoelkerung_kosten: int = None,
    beschreibung: str = None,
    token: str = None,
    admin=Depends(require_admin)
):
    """Update creature (admin only)."""
    conn = get_db()
    cur = conn.cursor()
    updates = []
    values = []
    if name is not None:
        updates.append("name = ?")
        values.append(name)
    if typ is not None:
        updates.append("typ = ?")
        values.append(typ)
    if staerke is not None:
        updates.append("staerke = ?")
        values.append(staerke)
    if gesundheit is not None:
        updates.append("gesundheit = ?")
        values.append(gesundheit)
    if bevoelkerung_kosten is not None:
        updates.append("bevoelkerung_kosten = ?")
        values.append(bevoelkerung_kosten)
    if beschreibung is not None:
        updates.append("beschreibung = ?")
        values.append(beschreibung)
    if not updates:
        raise HTTPException(400, "No fields to update")
    values.append(lebewesen_id)
    cur.execute(f"UPDATE lebewesen SET {', '.join(updates)} WHERE id = ?", values)
    conn.commit()
    conn.close()
    return {"message": "Lebewesen updated"}

@app.delete("/admin/lebewesen/{lebewesen_id}")
async def delete_lebewesen(
    lebewesen_id: int,
    token: str = None,
    admin=Depends(require_admin)
):
    """Delete creature (admin only)."""
    conn = get_db()
    cur = conn.cursor()
    cur.execute("DELETE FROM lebewesen WHERE id = ?", (lebewesen_id,))
    if cur.rowcount == 0:
        conn.close()
        raise HTTPException(404, "Lebewesen not found")
    conn.commit()
    conn.close()
    return {"message": "Lebewesen deleted"}

# ─── Admin: Regierungsformen ─────────────────────────────────────────────────────
@app.get("/admin/regierungsformen")
async def list_regierungsformen(token: str = None, admin=Depends(require_admin)):
    """List all government forms (admin only)."""
    conn = get_db()
    cur = conn.cursor()
    cur.execute("SELECT * FROM regierungsformen ORDER BY name")
    rows = cur.fetchall()
    conn.close()
    return [dict(r) for r in rows]

@app.post("/admin/regierungsformen")
async def create_regierungsform(
    name: str,
    beschreibung: str = "",
    bonus_malus: str = "{}",
    token: str = None,
    admin=Depends(require_admin)
):
    """Create new government form (admin only)."""
    import json
    conn = get_db()
    cur = conn.cursor()
    try:
        bonus_data = json.loads(bonus_malus) if isinstance(bonus_malus, str) else bonus_malus
        cur.execute("""
            INSERT INTO regierungsformen (name, beschreibung, bonus_malus)
            VALUES (?, ?, ?)
        """, (name, beschreibung, json.dumps(bonus_data)))
        conn.commit()
        regierungsform_id = cur.lastrowid
        conn.close()
        return {"message": f"Regierungsform {name} created", "regierungsform_id": regierungsform_id}
    except sqlite3.IntegrityError:
        conn.close()
        raise HTTPException(400, "Regierungsform already exists")

@app.put("/admin/regierungsformen/{regierungsform_id}")
async def update_regierungsform(
    regierungsform_id: int,
    name: str = None,
    beschreibung: str = None,
    bonus_malus: str = None,
    token: str = None,
    admin=Depends(require_admin)
):
    """Update government form (admin only)."""
    import json
    conn = get_db()
    cur = conn.cursor()
    updates = []
    values = []
    if name is not None:
        updates.append("name = ?")
        values.append(name)
    if beschreibung is not None:
        updates.append("beschreibung = ?")
        values.append(beschreibung)
    if bonus_malus is not None:
        bonus_data = json.loads(bonus_malus) if isinstance(bonus_malus, str) else bonus_malus
        updates.append("bonus_malus = ?")
        values.append(json.dumps(bonus_data))
    if not updates:
        raise HTTPException(400, "No fields to update")
    values.append(regierungsform_id)
    cur.execute(f"UPDATE regierungsformen SET {', '.join(updates)} WHERE id = ?", values)
    conn.commit()
    conn.close()
    return {"message": "Regierungsform updated"}

@app.delete("/admin/regierungsformen/{regierungsform_id}")
async def delete_regierungsform(
    regierungsform_id: int,
    token: str = None,
    admin=Depends(require_admin)
):
    """Delete government form (admin only)."""
    conn = get_db()
    cur = conn.cursor()
    cur.execute("DELETE FROM regierungsformen WHERE id = ?", (regierungsform_id,))
    if cur.rowcount == 0:
        conn.close()
        raise HTTPException(404, "Regierungsform not found")
    conn.commit()
    conn.close()
    return {"message": "Regierungsform deleted"}

# ─── Helpers ──────────────────────────────────────────────────────────────────
def safe_json(val, default):
    if isinstance(val, str):
        try: return json.loads(val)
        except: return default
    return val if val is not None else default

def get_provinz_or_403(cur, player_id: int, provinz_id: int):
    """Provinz laden und prüfen ob sie dem Spieler gehört."""
    cur.execute("SELECT * FROM provinzen WHERE id=?", (provinz_id,))
    p = cur.fetchone()
    if not p:
        raise HTTPException(404, f"Provinz {provinz_id} nicht gefunden")
    if p["player_id"] != player_id:
        raise HTTPException(403, "Diese Provinz gehört dir nicht")
    return p

def get_lager_menge(cur, provinz_id: int, ressource_id: int) -> int:
    cur.execute("SELECT menge FROM provinz_lager WHERE provinz_id=? AND ressource_id=?",
                (provinz_id, ressource_id))
    row = cur.fetchone()
    return row["menge"] if row else 0

def lager_set(cur, provinz_id: int, ressource_id: int, neue_menge: int):
    if neue_menge < 0:
        raise HTTPException(400, "Menge kann nicht negativ sein")
    if neue_menge == 0:
        cur.execute("DELETE FROM provinz_lager WHERE provinz_id=? AND ressource_id=?",
                    (provinz_id, ressource_id))
    else:
        cur.execute("""INSERT INTO provinz_lager (provinz_id, ressource_id, menge)
                       VALUES (?,?,?)
                       ON CONFLICT(provinz_id, ressource_id)
                       DO UPDATE SET menge=excluded.menge, updated_at=CURRENT_TIMESTAMP""",
                    (provinz_id, ressource_id, neue_menge))

def resolve_transports(cur):
    """Prüft alle Transporte auf Ankunft und überträgt die Waren in die Ziel-Lager."""
    cur.execute("SELECT * FROM handelskarren_transport WHERE status='unterwegs' AND ankunft_geplant <= CURRENT_TIMESTAMP")
    transports = cur.fetchall()
    for t in transports:
        # Waren hinzufügen
        ware = get_lager_menge(cur, t["nach_provinz_id"], t["ressource_id"])
        lager_set(cur, t["nach_provinz_id"], t["ressource_id"], ware + t["menge"])
        # Karren hinzufügen
        karren = get_lager_menge(cur, t["nach_provinz_id"], HANDELSKARREN_ID)
        lager_set(cur, t["nach_provinz_id"], HANDELSKARREN_ID, karren + t["karren_benoetigt"])
        # Status updaten
        cur.execute("UPDATE handelskarren_transport SET status='angekommen', angekommen_at=CURRENT_TIMESTAMP WHERE id=?", (t["id"],))

def fmt_provinz(r):
    return {"id":r["id"],"player_id":r["player_id"],
            "world_x":r["world_x"],"world_y":r["world_y"],
            "name":r["name"] or f"Provinz ({r['world_x']},{r['world_y']})",
            "created_at":r["created_at"]}

def fmt_lager_eintrag(r):
    return {"ressource_id":r["ressource_id"],"ressource_name":r["ressource_name"],
            "typ":r["typ"],"wert":r["wert"],"platzbedarf":r["platzbedarf"],
            "menge":r["menge"],"gesamtwert":r["menge"]*r["wert"]}

def fmt_gebaeude(r):
    bautyp=r["bautyp"] or "Land"
    fmap={"Land":"gebaeude","Stadt":"stadt","Stadtausbau":"stadtausbau",
          "Weg":"weg","Wegkreuzung":"kreuzung","Vorgabe":"vorgabe"}
    return {"id":r["id"],"name":r["name"],"symbol_emoji":r["symbol_emoji"],
            "symbol_url":r["symbol_url"],"bild_url":r["bild_url"],
            "kategorie":r["kategorie"],"bautyp":bautyp,
            "provinz_feldtyp":fmap.get(bautyp),"baubar":bool(r["baubar"]),
            "ausbaubar":bool(r["ausbaubar"]),"unique_gebaeude":bool(r["unique_gebaeude"]),
            "nur_kueste":bool(r["nur_kueste"]),"ist_feld":bool(r["ist_feld"]),
            "tech_level":r["tech_level"],"baukosten_mips":r["baukosten_mips"],
            "ausbaukosten_mips":r["ausbaukosten_mips"],"energiebedarf":r["energiebedarf"],
            "arbeiter":r["arbeiter"],"zusatzarbeiter_pro_stufe":r["zusatzarbeiter_pro_stufe"],
            "wohnraum":r["wohnraum"],"zusatzwohnraum_pro_stufe":r["zusatzwohnraum_pro_stufe"],
            "lagerkapazitaet":r["lagerkapazitaet"],"beschreibung":r["beschreibung"],
            "rohstoffbedarf_bau":safe_json(r["rohstoffbedarf_bau"],[]),
            "rohstoffgrundbedarf_ausbau":safe_json(r["rohstoffgrundbedarf_ausbau"],[]),
            "rohstoffverbrauch":safe_json(r["rohstoffverbrauch"],[]),
            "produktion":safe_json(r["produktion"],[]),
            "terrain_effektivitaet":safe_json(r["terrain_effektivitaet"],{}),
            "vorkommen_effektivitaet":safe_json(r["vorkommen_effektivitaet"],{}),
            "spezial_eigenschaften":safe_json(r["spezial_eigenschaften"],{}),
            "schlachtfeld":safe_json(r["schlachtfeld"],{})}

def fmt_ressource(r):
    return {"id":r["id"],"name":r["name"],"typ":r["typ"],
            "wert":r["wert"],"verbrauch":r["verbrauch"],"platzbedarf":r["platzbedarf"]}

def fmt_vorkommen(r):
    return {"id":r["id"],"name":r["name"],"typ":r["typ"],"tech":r["tech"],
            "suchkosten":r["suchkosten"],"beschreibung":r["beschreibung"] or "",
            "findwahrscheinlichkeit":safe_json(r["findwahrscheinlichkeit"],{})}

# ─── Pydantic Models ──────────────────────────────────────────────────────────
class ProvinzCreate(BaseModel):
    world_x: int
    world_y: int
    name: Optional[str] = ""
    terrain: Optional[str] = "Grasland"

class ProvinzUpdate(BaseModel):
    name: str

class LagerUpdate(BaseModel):
    menge: int   # absolute neue Menge

class LagerDelta(BaseModel):
    delta: int   # +/- Änderung

class TransportRequest(BaseModel):
    nach_provinz_id: int
    ressource_id: int
    menge: int

class BuildingUpgrade(BaseModel):
    building_x: int
    building_y: int

class RoadUpgrade(BaseModel):
    crossing_x: Optional[int] = None
    crossing_y: Optional[int] = None
    road_x: Optional[int] = None
    road_y: Optional[int] = None

class RoadCreate(BaseModel):
    road_type: str
    x: int
    y: int

class BuildingCreate(BaseModel):
    building_type: str; x: int; y: int

# ─── Endpoints: Frontend ──────────────────────────────────────────────────────
@app.get("/")
async def root():
    return FileResponse("index.html")

# ─── Endpoints: Spieler ───────────────────────────────────────────────────────
@app.get("/player/{player_id}")
async def get_player(player_id: int):
    conn = get_db(); cur = conn.cursor()
    cur.execute("SELECT * FROM players WHERE id=?", (player_id,))
    p = cur.fetchone(); conn.close()
    if not p: raise HTTPException(404, "Spieler nicht gefunden")
    return {"id":p["id"],"name":p["name"],"iron":p["iron"],"steel":p["steel"],"fuel":p["fuel"]}

@app.post("/player/{player_id}/resources/produce")
@app.post("/player/{player_id}/resources/produce")
async def produce_resources(player_id: int, hours: int = 24, preview_only: bool = False):
    """
    Simuliert eine oder mehrere Produktionsstunden für den Spieler.
    In preview_only=True werden keine Daten in der DB geändert.
    """
    conn = get_db(); cur = conn.cursor()
    cur.execute("SELECT id, last_turn_timestamp FROM players WHERE id=?", (player_id,))
    player = cur.fetchone()
    if not player: conn.close(); raise HTTPException(404, "Spieler nicht gefunden")
    
    # Zeitguthaben prüfen (nur bei echtem Turn)
    if not preview_only:
        last_ts = datetime.strptime(player["last_turn_timestamp"], "%Y-%m-%d %H:%M:%S")
        now = datetime.now()
        credit_seconds = (now - last_ts).total_seconds()
        if credit_seconds < hours * 3600:
            conn.close()
            raise HTTPException(400, f"Nicht genug Zeitguthaben. Verfügbar: {int(credit_seconds//3600)}h")

    # Vor der Produktion alle fälligen Transporte abschließen (nur bei echtem Turn)
    if not preview_only:
        resolve_transports(cur)
    
    # 1. Basis-Daten laden
    cur.execute("SELECT id, name, platzbedarf FROM ressourcen")
    res_rows = cur.fetchall()
    res_map_name_to_id = {r["name"].lower(): r["id"] for r in res_rows}
    res_map_id_to_platz = {r["id"]: r["platzbedarf"] for r in res_rows}
    
    cur.execute("SELECT name, lagerkapazitaet, rohstoffverbrauch, produktion, terrain_effektivitaet, arbeiter, wohnraum FROM gebaeude_typen")
    gt_rows = cur.fetchall()
    gt_map = {gt["name"]: dict(gt) for gt in gt_rows}
    for k in gt_map:
        gt_map[k]["verbrauch"] = safe_json(gt_map[k]["rohstoffverbrauch"], [])
        gt_map[k]["produktion"] = safe_json(gt_map[k]["produktion"], [])
        gt_map[k]["terrain_eff"] = safe_json(gt_map[k].get("terrain_effektivitaet"), {})
        
    cur.execute("SELECT id, name, world_x, world_y, terrain FROM provinzen WHERE player_id=?", (player_id,))
    provinzen = cur.fetchall()
    
    bericht = []
    
    # Wir loopen über die Stunden, um den kumulativen Effekt zu simulieren
    # (besonders wichtig für Rohstoffmangel im Verlauf einer langen Simulation)
    for prov in provinzen:
        prov_id = prov["id"]
        prov_terrain = prov["terrain"] or "Grasland"
        cur.execute("SELECT building_x, building_y, building_type, level FROM buildings WHERE world_x=? AND world_y=?", 
                    (prov["world_x"], prov["world_y"]))
        buildings = cur.fetchall()
        
        # Lagerbestand laden
        cur.execute("SELECT ressource_id, menge FROM provinz_lager WHERE provinz_id=?", (prov_id,))
        lager = {r["ressource_id"]: r["menge"] for r in cur.fetchall()}
        
        # Kapazitäts-Berechnung & Arbeiter/Wohnraum Statistik
        kapazitaet = 1000  # Basis-Kapazität
        total_wohnraum = 0
        total_arbeiter_bedarf = 0
        
        for b in buildings:
            if b["building_type"] in gt_map:
                cfg = gt_map[b["building_type"]]
                lvl = b["level"] or 1
                kapazitaet += int(cfg.get("lagerkapazitaet", 0) or 0) * lvl
                total_wohnraum += int(cfg.get("wohnraum", 0) or 0) * lvl
                total_arbeiter_bedarf += int(cfg.get("arbeiter", 0) or 0) * lvl
        
        bevoelkerung = total_wohnraum
        effizienz = 1.0
        if total_arbeiter_bedarf > bevoelkerung and total_arbeiter_bedarf > 0:
            effizienz = bevoelkerung / total_arbeiter_bedarf

        # Kumulative Delta-Werte für Bericht
        delta_lager = {} 
        
        for _ in range(hours):
            def get_used_platz(lager_dict):
                return sum(menge * res_map_id_to_platz.get(rid, 1) for rid, menge in lager_dict.items())
            
            # Produktions-Logik pro Gebäude
            for b in buildings:
                b_type = b["building_type"]
                if b_type not in gt_map: continue
                
                cfg = gt_map[b_type]
                lvl = b["level"] or 1
                verbrauch = cfg["verbrauch"]
                prod_list = cfg["produktion"]
                
                # 1. Verbrauch prüfen
                mangel = False
                for v in verbrauch:
                    r_name = (v.get("ressource") or v.get("name", "")).lower()
                    r_id = res_map_name_to_id.get(r_name)
                    # Werte in DB sind pro Tag (24h), daher durch 24 teilen
                    menge_soll = (v.get("menge", 0) / 24) * lvl
                    if r_id and lager.get(r_id, 0) < menge_soll:
                        mangel = True; break
                
                if mangel: continue
                    
                # Verbrauch abziehen
                for v in verbrauch:
                    r_name = (v.get("ressource") or v.get("name", "")).lower()
                    r_id = res_map_name_to_id.get(r_name)
                    if r_id: 
                        menge_v = (v.get("menge", 0) / 24) * lvl
                        lager[r_id] -= menge_v
                        delta_lager[r_id] = delta_lager.get(r_id, 0) - menge_v
                
                # 2. Produktion berechnen
                for p in prod_list:
                    r_id = res_map_name_to_id.get((p.get("ressource") or p.get("name", "")).lower())
                    if not r_id: continue
                    
                    terrain_bonus = gt_map[b_type]["terrain_eff"].get(prov_terrain, 100) / 100.0
                    # Werte in DB sind pro Tag (24h), daher durch 24 teilen
                    menge_pro_stunde = p.get("menge", 0) / 24
                    menge_brutto = menge_pro_stunde * lvl * effizienz * terrain_bonus
                    
                    belegt = get_used_platz(lager)
                    frei = kapazitaet - belegt
                    platz_pro_e = res_map_id_to_platz.get(r_id, 1)
                    
                    if frei <= 0: break
                    tats_menge = min(menge_brutto, math.floor(frei / platz_pro_e))
                    if tats_menge > 0:
                        lager[r_id] = lager.get(r_id, 0) + tats_menge
                        delta_lager[r_id] = delta_lager.get(r_id, 0) + tats_menge
        
        prov_bericht = {
            "provinz_id": prov_id,
            "name": prov["name"] or f"({prov['world_x']},{prov['world_y']})",
            "terrain": prov_terrain,
            "effizienz": round(effizienz, 2),
            "stats": {"wohnraum": total_wohnraum, "bedarf": total_arbeiter_bedarf, "bevoelkerung": bevoelkerung},
            "deltas": {rid: round(m, 2) for rid, m in delta_lager.items()},
            "neues_lager": {rid: round(m, 2) for rid, m in lager.items()}
        }
        bericht.append(prov_bericht)
        
        if not preview_only:
            for rid, m in lager.items():
                lager_set(cur, prov_id, rid, int(m))

    if not preview_only:
        # Timestamp aktualisieren: last_turn_timestamp = last_turn_timestamp + hours hours
        # In SQLite: datetime(last_turn_timestamp, '+X hours')
        cur.execute("UPDATE players SET last_turn_timestamp = datetime(last_turn_timestamp, ? || ' hours') WHERE id=?", 
                    (hours, player_id))
        conn.commit()
    
    conn.close()
    return {
        "message": "Simulation abgeschlossen" if preview_only else "Produktionsrunde abgeschlossen",
        "preview": preview_only,
        "hours": hours,
        "bericht": bericht
    }

@app.post("/player/{player_id}/roads/upgrade")
async def upgrade_road(player_id: int, upgrade: RoadUpgrade):
    conn = get_db(); cur = conn.cursor()
    cur.execute("SELECT iron FROM players WHERE id=?", (player_id,))
    player = cur.fetchone()
    if not player: conn.close(); raise HTTPException(404, "Spieler nicht gefunden")
    costs = CROSSING_COSTS if upgrade.road_type == "crossing" else ROAD_COSTS
    cost = costs.get(upgrade.new_level)
    if not cost: conn.close(); raise HTTPException(400, "Ungültiges Level")
    if player["iron"] < cost: conn.close(); raise HTTPException(400, "Nicht genug Eisen")
    try:
        cur.execute("SELECT id FROM roads WHERE player_id=? AND grid_x=? AND grid_y=?",
                    (player_id, upgrade.grid_x, upgrade.grid_y))
        ex = cur.fetchone()
        if ex: cur.execute("UPDATE roads SET level=?,updated_at=CURRENT_TIMESTAMP WHERE id=?",(upgrade.new_level,ex["id"]))
        else:  cur.execute("INSERT INTO roads (player_id,world_x,world_y,grid_x,grid_y,road_type,level) VALUES (?,25,25,?,?,?,?)",(player_id,upgrade.grid_x,upgrade.grid_y,upgrade.road_type,upgrade.new_level))
        cur.execute("UPDATE players SET iron=iron-? WHERE id=?", (cost, player_id))
        conn.commit()
        cur.execute("SELECT iron FROM players WHERE id=?", (player_id,))
        u = cur.fetchone(); conn.close()
        return {"message":f"Upgrade auf Level {upgrade.new_level}","remaining_iron":u["iron"]}
    except Exception as e: conn.rollback(); conn.close(); raise HTTPException(500, str(e))

@app.get("/player/{player_id}/production/stats")
async def get_production_stats(player_id: int):
    """Gibt eine Übersicht über die aktuelle Produktion/Verbrauch aller Provinzen."""
    conn = get_db(); cur = conn.cursor()
    cur.execute("SELECT id, name, world_x, world_y FROM provinzen WHERE player_id=?", (player_id,))
    provinces = cur.fetchall()
    
    stats = []
    for p in provinces:
        # Gebäude laden
        cur.execute("SELECT building_type, level FROM buildings WHERE world_x=? AND world_y=?", (p["world_x"], p["world_y"]))
        buildings = cur.fetchall()
        
        p_prod = {}
        p_cons = {}
        
        for b in buildings:
            cur.execute("SELECT produktion, rohstoffverbrauch FROM gebaeude_typen WHERE name=?", (b["building_type"],))
            gt = cur.fetchone()
            if not gt: continue
            
            lvl = b["level"] or 1
            prod_list = safe_json(gt["produktion"], [])
            cons_list = safe_json(gt["rohstoffverbrauch"], [])
            
            for item in prod_list:
                res_name = item.get("name")
                menge = item.get("menge", 0) * lvl
                p_prod[res_name] = p_prod.get(res_name, 0) + menge
                
            for item in cons_list:
                res_name = item.get("name")
                menge = item.get("menge", 0) * lvl
                p_cons[res_name] = p_cons.get(res_name, 0) + menge
                
        stats.append({
            "provinz_id": p["id"],
            "name": p["name"] or f"({p['world_x']},{p['world_y']})",
            "production": p_prod,
            "consumption": p_cons
        })
        
    conn.close()
    return {"player_id": player_id, "stats": stats}

@app.get("/player/{player_id}/province/{world_x}/{world_y}")
async def get_province_data(player_id: int, world_x: int, world_y: int):
    conn = get_db(); cur = conn.cursor()
    cur.execute("SELECT grid_x,grid_y,road_type,level FROM roads WHERE player_id=? AND world_x=? AND world_y=?",
                (player_id, world_x, world_y))
    roads = [{"grid_x":r["grid_x"],"grid_y":r["grid_y"],"road_type":r["road_type"],"level":r["level"]} for r in cur.fetchall()]
    cur.execute("SELECT building_x,building_y,building_type FROM buildings WHERE player_id=? AND world_x=? AND world_y=?",
                (player_id, world_x, world_y))
    bldgs = [{"building_x":b["building_x"],"building_y":b["building_y"],"building_type":b["building_type"],"icon":"🏗️"} for b in cur.fetchall()]
    conn.close()
    return {"roads":roads,"buildings":bldgs}

@app.post("/player/{player_id}/buildings")
async def build_building(player_id: int, building: BuildingCreate):
    conn = get_db(); cur = conn.cursor()
    cur.execute("SELECT iron FROM players WHERE id=?", (player_id,))
    player = cur.fetchone()
    if not player: conn.close(); raise HTTPException(404, "Spieler nicht gefunden")
    cost = BUILDING_COSTS.get(building.building_type)
    if cost is None: conn.close(); raise HTTPException(400, "Ungültiger Gebäude-Typ")
    
    if building.building_type == "building_bunker":
        cur.execute("SELECT id FROM buildings WHERE player_id=? AND (building_type='building_bunker' OR building_type='Bunker')", (player_id,))
        if cur.fetchone():
            conn.close(); raise HTTPException(400, "Bunker kann nur einmal pro Spieler gebaut werden")
    elif player["iron"] < cost:
        conn.close(); raise HTTPException(400, "Nicht genug Eisen")
    
    try:
        cur.execute("INSERT INTO buildings (player_id,world_x,world_y,building_x,building_y,building_type) VALUES (?,25,25,?,?,?)",
                    (player_id, building.x, building.y, building.building_type))
        if cost > 0:
            cur.execute("UPDATE players SET iron=iron-? WHERE id=?", (cost, player_id))
        conn.commit()
        cur.execute("SELECT iron FROM players WHERE id=?", (player_id,))
        u = cur.fetchone(); conn.close()
        return {"message":f"{building.building_type} gebaut","remaining_iron":u["iron"]}
    except sqlite3.IntegrityError: conn.close(); raise HTTPException(400, "Feld bereits bebaut")
    except Exception as e: conn.rollback(); conn.close(); raise HTTPException(500, str(e))

@app.delete("/player/{player_id}/buildings/{bx}/{by}")
async def remove_building(player_id: int, bx: int, by: int):
    conn = get_db(); cur = conn.cursor()
    try:
        cur.execute("DELETE FROM buildings WHERE player_id=? AND world_x=25 AND world_y=25 AND building_x=? AND building_y=?",
                    (player_id, bx, by))
        if cur.rowcount == 0: conn.close(); raise HTTPException(404, "Gebäude nicht gefunden")
        conn.commit(); conn.close()
        return {"message":"Gebäude entfernt"}
    except Exception as e: conn.rollback(); conn.close(); raise HTTPException(500, str(e))

WAY_TYPES = ["Feldweg", "Feldwegkreuzung", "Kiesweg", "Kieskreuzung"]

@app.post("/player/{player_id}/roads")
async def build_road(player_id: int, road: RoadCreate):
    conn = get_db(); cur = conn.cursor()
    cur.execute("SELECT iron FROM players WHERE id=?", (player_id,))
    player = cur.fetchone()
    if not player: conn.close(); raise HTTPException(404, "Spieler nicht gefunden")
    
    if road.road_type not in WAY_TYPES:
        conn.close(); raise HTTPException(400, "Ungültiger Weg-Typ")
    
    cost = BUILDING_COSTS.get(road.road_type, 0)
    if player["iron"] < cost:
        conn.close(); raise HTTPException(400, "Nicht genug Eisen")
    
    is_crossing = "kreuzung" in road.road_type.lower()
    road_type_db = "crossing" if is_crossing else "road"
    
    try:
        cur.execute("""INSERT INTO roads (player_id,world_x,world_y,grid_x,grid_y,road_type,level) 
                       VALUES (?,25,25,?,?,?,1)""",
                    (player_id, road.x, road.y, road_type_db))
        cur.execute("UPDATE players SET iron=iron-? WHERE id=?", (cost, player_id))
        conn.commit()
        cur.execute("SELECT iron FROM players WHERE id=?", (player_id,))
        u = cur.fetchone(); conn.close()
        return {"message":f"{road.road_type} gebaut","remaining_iron":u["iron"]}
    except sqlite3.IntegrityError: conn.close(); raise HTTPException(400, "Feld bereits belegt")
    except Exception as e: conn.rollback(); conn.close(); raise HTTPException(500, str(e))

@app.get("/player/{player_id}/credit")
async def get_player_credit(player_id: int):
    conn = get_db(); cur = conn.cursor()
    cur.execute("SELECT last_turn_timestamp FROM players WHERE id=?", (player_id,))
    row = cur.fetchone()
    if not row: conn.close(); raise HTTPException(404, "Spieler nicht gefunden")
    
    # SQLite timestamp string -> datetime
    last_ts_str = row["last_turn_timestamp"]
    try:
        last_ts = datetime.strptime(last_ts_str, "%Y-%m-%d %H:%M:%S")
    except ValueError:
        # Falls UTC Format mit T Z (ISO)
        last_ts = datetime.fromisoformat(last_ts_str.replace("Z", "+00:00")).replace(tzinfo=None)
        
    now = datetime.now()
    diff = now - last_ts
    hours = int(diff.total_seconds() // 3600)
    hours = min(hours, 240) # max 10 tage
    
    conn.close()
    return {"player_id": player_id, "credit_hours": hours, "now": now.strftime("%Y-%m-%d %H:%M:%S"), "last_turn": last_ts_str}

@app.get("/player/{player_id}/resources/total")
async def get_total_resources(player_id: int):
    """Summiert alle Ressourcen aus allen Provinzen des Spielers plus Basis-Werte."""
    conn = get_db(); cur = conn.cursor()
    cur.execute("SELECT name, iron, steel, fuel FROM players WHERE id=?", (player_id,))
    player = cur.fetchone()
    if not player: conn.close(); raise HTTPException(404, "Spieler nicht gefunden")
    
    # Ressourcen aus Lagern summieren
    cur.execute("""SELECT r.name, SUM(pl.menge) as gesamt 
                   FROM provinz_lager pl JOIN ressourcen r ON pl.ressource_id = r.id 
                   JOIN provinzen p ON pl.provinz_id = p.id
                   WHERE p.player_id=? GROUP BY r.id""", (player_id,))
    lager_sums = {row["name"].lower(): row["gesamt"] for row in cur.fetchall()}
    
    # Zusammenfügen (Legacy-Spalten + Lager-Summen)
    res = {
        "iron": int(player["iron"] or 0) + int(lager_sums.get("eisen", 0)),
        "steel": int(player["steel"] or 0) + int(lager_sums.get("stahl", 0)),
        "fuel": int(player["fuel"] or 0) + int(lager_sums.get("brennstoff", 0)),
        "name": player["name"]
    }
    conn.close()
    return res

@app.get("/player/{player_id}/provinzen")
async def get_provinzen(player_id: int):
    """Alle Provinzen eines Spielers."""
    conn = get_db(); cur = conn.cursor()
    resolve_transports(cur); conn.commit()
    cur.execute("SELECT id FROM players WHERE id=?", (player_id,))
    if not cur.fetchone(): conn.close(); raise HTTPException(404, "Spieler nicht gefunden")
    cur.execute("SELECT * FROM provinzen WHERE player_id=? ORDER BY id", (player_id,))
    provinzen = [fmt_provinz(r) for r in cur.fetchall()]
    conn.close()
    return {"player_id":player_id,"provinzen":provinzen,"anzahl":len(provinzen)}

@app.get("/world/provinzen")
async def get_world_provinzen():
    """Alle beanspruchten Provinzen der Welt (für Ziel-Auswahl)."""
    conn = get_db(); cur = conn.cursor()
    cur.execute("SELECT p.id, p.player_id, p.world_x, p.world_y, p.name, pl.name as player_name FROM provinzen p LEFT JOIN players pl ON p.player_id=pl.id")
    provinzen = [{"id":r["id"], "player_id":r["player_id"], "player_name": r["player_name"], "world_x":r["world_x"], "world_y":r["world_y"], "name":r["name"]} for r in cur.fetchall()]
    conn.close()
    return {"provinzen": provinzen}

@app.post("/player/{player_id}/provinzen")
async def provinz_beanspruchen(player_id: int, data: ProvinzCreate):
    """Eine Weltkarte-Provinz beanspruchen (muss noch unbesetzt sein)."""
    conn = get_db(); cur = conn.cursor()
    cur.execute("SELECT id FROM players WHERE id=?", (player_id,))
    if not cur.fetchone(): conn.close(); raise HTTPException(404, "Spieler nicht gefunden")
    cur.execute("SELECT id,player_id FROM provinzen WHERE world_x=? AND world_y=?",
                (data.world_x, data.world_y))
    ex = cur.fetchone()
    if ex:
        conn.close()
        if ex["player_id"] == player_id:
            raise HTTPException(409, "Du besitzt diese Provinz bereits")
        raise HTTPException(409, f"Diese Provinz gehört bereits Spieler {ex['player_id']}")
    try:
        cur.execute("INSERT INTO provinzen (player_id,world_x,world_y,name,terrain) VALUES (?,?,?,?,?)",
                    (player_id, data.world_x, data.world_y, data.name or "", data.terrain or "Grasland"))
        provinz_id = cur.lastrowid
        conn.commit()
        cur.execute("SELECT * FROM provinzen WHERE id=?", (provinz_id,))
        p = cur.fetchone(); conn.close()
        return {"message":"Provinz beansprucht","provinz":fmt_provinz(p)}
    except Exception as e: conn.rollback(); conn.close(); raise HTTPException(500, str(e))

@app.patch("/player/{player_id}/provinzen/{provinz_id}")
async def update_provinz_name(player_id: int, provinz_id: int, prov_update: ProvinzUpdate):
    conn = get_db(); cur = conn.cursor()
    cur.execute("UPDATE provinzen SET name=? WHERE id=? AND player_id=?", (prov_update.name, provinz_id, player_id))
    if cur.rowcount == 0:
        conn.close()
        raise HTTPException(404, "Provinz nicht gefunden oder gehört nicht Spieler")
    conn.commit(); conn.close()
    return {"status": "success", "new_name": prov_update.name}

@app.get("/player/{player_id}/provinzen/{provinz_id}")
async def get_provinz(player_id: int, provinz_id: int):
    conn = get_db(); cur = conn.cursor()
    cur.execute("SELECT * FROM provinzen WHERE id=? AND player_id=?", (provinz_id, player_id))
    prov = cur.fetchone()
    if not prov: conn.close(); raise HTTPException(404, "Provinz nicht gefunden")
    
    resolve_transports(cur)
    
    # Gebäude laden
    cur.execute("SELECT building_x, building_y, building_type, level FROM buildings WHERE world_x=? AND world_y=?", (prov["world_x"], prov["world_y"]))
    buildings = [dict(b) for b in cur.fetchall()]
    
    # Lagerzustand (für Gesamtübersicht)
    cur.execute("""SELECT r.name, pl.menge FROM provinz_lager pl 
                   JOIN ressourcen r ON pl.ressource_id = r.id 
                   WHERE pl.provinz_id=?""", (provinz_id,))
    lager = [dict(l) for l in cur.fetchall()]
    
    conn.close()
    return {
        "id": prov["id"], "name": prov["name"], "world_x": prov["world_x"], "world_y": prov["world_y"],
        "buildings": buildings,
        "lager": lager
    }

@app.post("/player/{player_id}/provinzen/{provinz_id}/build")
async def build_in_province(player_id: int, provinz_id: int, building: BuildingCreate):
    conn = get_db(); cur = conn.cursor()
    
    # Prüfen ob Spieler existiert
    cur.execute("SELECT iron FROM players WHERE id=?", (player_id,))
    player = cur.fetchone()
    if not player: conn.close(); raise HTTPException(404, "Spieler nicht gefunden")
    
    # Prüfen ob Province dem Spieler gehört
    cur.execute("SELECT world_x, world_y, terrain FROM provinzen WHERE id=? AND player_id=?", (provinz_id, player_id))
    prov = cur.fetchone()
    if not prov: conn.close(); raise HTTPException(404, "Provinz nicht gefunden oder gehört nicht dir")
    
    # Kosten ermitteln
    cost = BUILDING_COSTS.get(building.building_type)
    if cost is None:
        # Versuche mit Namen aus gebaeude_typen
        cur.execute("SELECT baukosten_mips FROM gebaeude_typen WHERE name=?", (building.building_type,))
        row = cur.fetchone()
        if row:
            cost = row["baukosten_mips"]
        else:
            conn.close(); raise HTTPException(400, "Ungültiger Gebäude-Typ")
    
    # Bunker-Spezialfall: einmalig pro Spieler, kostenlos
    if building.building_type == "building_bunker" or building.building_type == "Bunker":
        cur.execute("SELECT id FROM buildings WHERE player_id=? AND (building_type='building_bunker' OR building_type='Bunker')", (player_id,))
        if cur.fetchone():
            conn.close(); raise HTTPException(400, "Bunker kann nur einmal pro Spieler gebaut werden")
        cost = 0  # Kostenlos
    
    # Eisen-Prüfung (wenn Kosten > 0)
    if cost > 0 and player["iron"] < cost:
        conn.close(); raise HTTPException(400, f"Nicht genug Eisen. Benötigt: {cost}")
    
    # Prüfen ob Feld bereits belegt
    cur.execute("""SELECT id FROM buildings 
                   WHERE player_id=? AND world_x=? AND world_y=? AND building_x=? AND building_y=?""",
                (player_id, prov["world_x"], prov["world_y"], building.x, building.y))
    if cur.fetchone():
        conn.close(); raise HTTPException(400, "Feld bereits bebaut")
    
    try:
        # Gebäude einfügen
        cur.execute("""INSERT INTO buildings (player_id, world_x, world_y, building_x, building_y, building_type, level) 
                       VALUES (?, ?, ?, ?, ?, ?, 1)""",
                    (player_id, prov["world_x"], prov["world_y"], building.x, building.y, building.building_type))
        
        # Eisen abziehen wenn Kosten > 0
        if cost > 0:
            cur.execute("UPDATE players SET iron=iron-? WHERE id=?", (cost, player_id))
        
        conn.commit()
        
        # Aktualisierten Eisen-Stand abrufen
        cur.execute("SELECT iron FROM players WHERE id=?", (player_id,))
        new_iron = cur.fetchone()["iron"]
        conn.close()
        
        return {"message": f"{building.building_type} gebaut", "cost": cost, "remaining_iron": new_iron}
    except sqlite3.IntegrityError:
        conn.close(); raise HTTPException(400, "Feld bereits bebaut")
    except Exception as e:
        conn.rollback(); conn.close(); raise HTTPException(500, str(e))

@app.post("/player/{player_id}/provinzen/{provinz_id}/upgrade")
async def upgrade_building(player_id: int, provinz_id: int, req: BuildingUpgrade):
    conn = get_db(); cur = conn.cursor()
    # Provinz & Gebäude prüfen
    cur.execute("SELECT world_x, world_y FROM provinzen WHERE id=? AND player_id=?", (provinz_id, player_id))
    prov = cur.fetchone()
    if not prov: conn.close(); raise HTTPException(404, "Provinz nicht gefunden")
    
    cur.execute("SELECT building_type, level FROM buildings WHERE world_x=? AND world_y=? AND building_x=? AND building_y=?", 
                (prov["world_x"], prov["world_y"], req.building_x, req.building_y))
    b = cur.fetchone()
    if not b: conn.close(); raise HTTPException(404, "Gebäude nicht gefunden")
    
    # Typ-Infos (Kosten etc.)
    cur.execute("SELECT ausbaubar FROM gebaeude_typen WHERE name=?", (b["building_type"],))
    gt = cur.fetchone()
    if not gt or not gt["ausbaubar"]: conn.close(); raise HTTPException(400, "Gebäude nicht ausbaubar")
    
    # Kosten berechnen (vereinfacht: Level * 100 Eisen)
    new_level = (b["level"] or 1) + 1
    kosten_eisen = new_level * 100
    
    cur.execute("SELECT id FROM ressourcen WHERE name='Eisen'")
    res_eisen = cur.fetchone()
    if not res_eisen: conn.close(); raise HTTPException(500, "Eisen-Ressource nicht definiert")
    
    # Lager prüfen
    cur.execute("SELECT menge FROM provinz_lager WHERE provinz_id=? AND ressource_id=?", (provinz_id, res_eisen["id"]))
    l_eisen = cur.fetchone()
    if not l_eisen or l_eisen["menge"] < kosten_eisen:
        conn.close(); raise HTTPException(400, f"Nicht genug Eisen! Benötigt: {kosten_eisen}, Vorhanden: {l_eisen['menge'] if l_eisen else 0}")
        
    # Abziehen & Upgraden
    cur.execute("UPDATE provinz_lager SET menge = menge - ? WHERE provinz_id=? AND ressource_id=?", 
                (kosten_eisen, provinz_id, res_eisen["id"]))
    cur.execute("UPDATE buildings SET level=? WHERE world_x=? AND world_y=? AND building_x=? AND building_y=?", 
                (new_level, prov["world_x"], prov["world_y"], req.building_x, req.building_y))
    
    conn.commit(); conn.close()
    return {"status": "success", "new_level": new_level}

# ─── Endpoints: Provinz-Lager ─────────────────────────────────────────────────
@app.get("/player/{player_id}/provinzen/{provinz_id}/lager")
async def get_lager(player_id: int, provinz_id: int, typ: Optional[str] = None):
    """Ressourcen-Lager einer Provinz (nur eigene Provinzen)."""
    conn = get_db(); cur = conn.cursor()
    resolve_transports(cur); conn.commit()
    p = get_provinz_or_403(cur, player_id, provinz_id)
    
    sql = """SELECT pl.ressource_id, r.name as ressource_name, r.typ, r.wert, r.platzbedarf, pl.menge
             FROM provinz_lager pl
             JOIN ressourcen r ON pl.ressource_id = r.id
             WHERE pl.provinz_id=? AND pl.menge>0"""
    params = [provinz_id]
    if typ:
        sql += " AND r.typ=?"; params.append(typ)
    sql += " ORDER BY r.typ, r.name"
    cur.execute(sql, params)
    eintraege = [fmt_lager_eintrag(r) for r in cur.fetchall()]
    gesamtwert = sum(e["gesamtwert"] for e in eintraege)
    
    # Kapazität berechnen
    cur.execute("SELECT building_type FROM buildings WHERE player_id=? AND world_x=? AND world_y=?",
                (player_id, p["world_x"], p["world_y"]))
    buildings = cur.fetchall()
    
    kapazitaet = 1000
    for b in buildings:
        cur.execute("SELECT lagerkapazitaet FROM gebaeude_typen WHERE name=?", (b["building_type"],))
        gt = cur.fetchone()
        if gt: kapazitaet += gt["lagerkapazitaet"]
    
    conn.close()
    return {"provinz_id":provinz_id,"eintraege":eintraege,
            "anzahl_positionen":len(eintraege),"gesamtwert":gesamtwert, "kapazitaet": kapazitaet}

@app.put("/player/{player_id}/provinzen/{provinz_id}/lager/{ressource_id}")
async def lager_ressource_setzen(player_id: int, provinz_id: int, ressource_id: int, data: LagerUpdate):
    """Absolute Menge einer Ressource im Lager setzen."""
    conn = get_db(); cur = conn.cursor()
    get_provinz_or_403(cur, player_id, provinz_id)
    cur.execute("SELECT id,name FROM ressourcen WHERE id=?", (ressource_id,))
    res = cur.fetchone()
    if not res: conn.close(); raise HTTPException(404, "Ressource nicht gefunden")
    if data.menge < 0: conn.close(); raise HTTPException(400, "Menge darf nicht negativ sein")
    try:
        lager_set(cur, provinz_id, ressource_id, data.menge)
        conn.commit(); conn.close()
        return {"message":f"{res['name']}: Menge auf {data.menge} gesetzt",
                "provinz_id":provinz_id,"ressource_id":ressource_id,"menge":data.menge}
    except Exception as e: conn.rollback(); conn.close(); raise HTTPException(500, str(e))

@app.patch("/player/{player_id}/provinzen/{provinz_id}/lager/{ressource_id}")
async def lager_ressource_aendern(player_id: int, provinz_id: int, ressource_id: int, data: LagerDelta):
    """Menge einer Ressource um delta ändern (+/-)."""
    conn = get_db(); cur = conn.cursor()
    get_provinz_or_403(cur, player_id, provinz_id)
    cur.execute("SELECT id,name FROM ressourcen WHERE id=?", (ressource_id,))
    res = cur.fetchone()
    if not res: conn.close(); raise HTTPException(404, "Ressource nicht gefunden")
    alte_menge = get_lager_menge(cur, provinz_id, ressource_id)
    neue_menge = alte_menge + data.delta
    if neue_menge < 0:
        conn.close()
        raise HTTPException(400, f"Nicht genug {res['name']} im Lager (vorhanden: {alte_menge}, benötigt: {-data.delta})")
    try:
        lager_set(cur, provinz_id, ressource_id, neue_menge)
        conn.commit(); conn.close()
        return {"message":f"{res['name']}: {alte_menge} → {neue_menge}",
                "provinz_id":provinz_id,"ressource_id":ressource_id,
                "alte_menge":alte_menge,"neue_menge":neue_menge,"delta":data.delta}
    except Exception as e: conn.rollback(); conn.close(); raise HTTPException(500, str(e))

# ─── Endpoints: Handelskarren-Transport ───────────────────────────────────────
@app.post("/player/{player_id}/provinzen/{provinz_id}/transport")
async def transport_senden(player_id: int, provinz_id: int, data: TransportRequest):
    """
    Ressourcen per Handelskarren von einer Provinz in eine andere transportieren.
    Target-Provinz darf auch von einem fremden Spieler sein.
    Limit: 1 Transport pro Lagerhütte der Provinz.
    """
    if data.menge <= 0:
        raise HTTPException(400, "Menge muss > 0 sein")
    if data.nach_provinz_id == provinz_id:
        raise HTTPException(400, "Quell- und Ziel-Provinz sind identisch")

    conn = get_db(); cur = conn.cursor()
    resolve_transports(cur)

    # Quell-Provinz prüfen
    von_p = get_provinz_or_403(cur, player_id, provinz_id)
    
    # Ziel-Provinz (darf wem anders gehören)
    cur.execute("SELECT * FROM provinzen WHERE id=?", (data.nach_provinz_id,))
    nach_p = cur.fetchone()
    if not nach_p:
        conn.close()
        raise HTTPException(404, "Ziel-Provinz nicht gefunden")

    # Ressource prüfen
    cur.execute("SELECT * FROM ressourcen WHERE id=?", (data.ressource_id,))
    res = cur.fetchone()
    if not res: conn.close(); raise HTTPException(404, "Ressource nicht gefunden")

    if data.ressource_id == HANDELSKARREN_ID:
        conn.close()
        raise HTTPException(400, "Handelskarren können nicht als Ware transportiert werden.")

    # Gebäude Limit (Lagerhütte) - Berücksichtigt Level
    cur.execute("SELECT SUM(level) as c FROM buildings WHERE player_id=? AND world_x=? AND world_y=? AND building_type='Lagerhütte'", 
                (player_id, von_p["world_x"], von_p["world_y"]))
    max_transporte = cur.fetchone()["c"] or 0
    cur.execute("SELECT COUNT(*) as c FROM handelskarren_transport WHERE von_provinz_id=? AND status='unterwegs'", (provinz_id,))
    aktive_transporte = cur.fetchone()["c"]
    
    if max_transporte <= 0:
        conn.close()
        raise HTTPException(400, "In dieser Provinz existiert keine Lagerhütte, Transporte sind unmöglich.")
    if aktive_transporte >= max_transporte:
        conn.close()
        raise HTTPException(400, f"Transport-Limit erreicht! {aktive_transporte} aktive Transporte bei {max_transporte} Lagerhütte(n)-Level.")

    # Verfügbare Menge prüfen
    vorhandene_menge = get_lager_menge(cur, provinz_id, data.ressource_id)
    if vorhandene_menge < data.menge:
        conn.close()
        raise HTTPException(400, f"Nicht genug {res['name']} in Provinz {von_p['name'] or provinz_id}")

    # Kapazität Ziel prüfen
    cur.execute("SELECT building_type FROM buildings WHERE world_x=? AND world_y=?", (nach_p["world_x"], nach_p["world_y"]))
    ziel_buildings = cur.fetchall()
    ziel_max_cap = 1000
    for b in ziel_buildings:
        cur.execute("SELECT lagerkapazitaet FROM gebaeude_typen WHERE name=?", (b["building_type"],))
        gt = cur.fetchone()
        if gt: ziel_max_cap += gt["lagerkapazitaet"]
        
    cur.execute("SELECT pl.ressource_id, pl.menge, r.platzbedarf FROM provinz_lager pl JOIN ressourcen r ON pl.ressource_id = r.id WHERE pl.provinz_id=?", (nach_p["id"],))
    ziel_lager_belegt = sum(i["menge"] * i["platzbedarf"] for i in cur.fetchall())

    cur.execute("SELECT platzbedarf FROM ressourcen WHERE id=?", (HANDELSKARREN_ID,))
    karren_platzbedarf = cur.fetchone()["platzbedarf"]

    platz_benoetigt = data.menge * res["platzbedarf"]
    karren_benoetigt = math.ceil(platz_benoetigt / HANDELSKARREN_KAPAZITÄT)
    incoming_platz = platz_benoetigt + (karren_benoetigt * karren_platzbedarf)
    
    if ziel_lager_belegt + incoming_platz > ziel_max_cap:
        conn.close()
        raise HTTPException(400, f"Ziel-Kapazität überschritten! Frei: {ziel_max_cap - ziel_lager_belegt}, Benötigt: {incoming_platz}")

    # Handelskarren vorhanden?
    karren_vorhanden = get_lager_menge(cur, provinz_id, HANDELSKARREN_ID)
    if karren_vorhanden < karren_benoetigt:
        conn.close()
        raise HTTPException(400, f"Nicht genug Handelskarren. Benötigt: {karren_benoetigt}, Vorhanden: {karren_vorhanden}")

    try:
        dist_x = abs(von_p["world_x"] - nach_p["world_x"])
        dist_y = abs(von_p["world_y"] - nach_p["world_y"])
        distanz = dist_x + dist_y
        delay_minuten = distanz * 10
        ankunft_geplant = datetime.utcnow() + timedelta(minutes=delay_minuten)

        # Quell-Lager: Ware + Karren abziehen
        lager_set(cur, provinz_id, data.ressource_id, vorhandene_menge - data.menge)
        lager_set(cur, provinz_id, HANDELSKARREN_ID, karren_vorhanden - karren_benoetigt)

        # Transport-Log
        cur.execute("""INSERT INTO handelskarren_transport
                       (player_id,von_provinz_id,nach_provinz_id,ressource_id,menge,karren_benoetigt,status,distanz,delay_minuten,ankunft_geplant)
                       VALUES (?,?,?,?,?,?,'unterwegs',?,?,?)""",
                    (player_id,provinz_id,data.nach_provinz_id,data.ressource_id,data.menge,karren_benoetigt,distanz,delay_minuten,ankunft_geplant.strftime('%Y-%m-%d %H:%M:%S')))
        transport_id = cur.lastrowid
        conn.commit()

        return {
            "message": f"{data.menge}× {res['name']} auf dem Weg. Dauert {delay_minuten} Minuten.",
            "transport_id": transport_id,
            "distanz": distanz,
            "delay_minuten": delay_minuten,
            "ankunft_geplant": ankunft_geplant.strftime('%H:%M'),
            "karren_benutzt": karren_benoetigt,
            "platz_benutzt": platz_benoetigt
        }
    except HTTPException: conn.rollback(); conn.close(); raise
    except Exception as e: conn.rollback(); conn.close(); raise HTTPException(500, str(e))

@app.get("/player/{player_id}/transport")
async def get_transporte(player_id: int, limit: int = 50):
    """Transport-Verlauf eines Spielers (neueste zuerst)."""
    conn = get_db(); cur = conn.cursor()
    cur.execute("SELECT id FROM players WHERE id=?", (player_id,))
    if not cur.fetchone(): conn.close(); raise HTTPException(404, "Spieler nicht gefunden")
    cur.execute("""
        SELECT t.id, t.menge, t.karren_benoetigt, t.status, t.created_at,
               r.name as ressource_name, r.typ as ressource_typ,
               vp.world_x as von_x, vp.world_y as von_y, vp.name as von_name,
               np.world_x as nach_x, np.world_y as nach_y, np.name as nach_name
        FROM handelskarren_transport t
        JOIN ressourcen r ON t.ressource_id=r.id
        JOIN provinzen vp ON t.von_provinz_id=vp.id
        JOIN provinzen np ON t.nach_provinz_id=np.id
        WHERE t.player_id=?
        ORDER BY t.id DESC LIMIT ?
    """, (player_id, limit))
    rows = cur.fetchall(); conn.close()
    return {"player_id":player_id,"transporte":[{
        "id":r["id"],"ressource":r["ressource_name"],"typ":r["ressource_typ"],
        "menge":r["menge"],"karren":r["karren_benoetigt"],"status":r["status"],
        "von": f"{r['von_name'] or f'({r["von_x"]},{r["von_y"]})'} ({r['von_x']},{r['von_y']})",
        "nach":f"{r['nach_name'] or f'({r["nach_x"]},{r["nach_y"]})'} ({r['nach_x']},{r['nach_y']})",
        "datum":r["created_at"]
    } for r in rows]}

# ─── Endpoints: Gebäude-Typen ─────────────────────────────────────────────────
@app.get("/gebaeude")
async def get_gebaeude_typen(kategorie: Optional[str]=None, bautyp: Optional[str]=None,
                              baubar: Optional[bool]=None, terrain: Optional[str]=None):
    conn = get_db(); cur = conn.cursor()
    sql = "SELECT * FROM gebaeude_typen WHERE 1=1"; params = []
    if kategorie: sql+=" AND kategorie=?"; params.append(kategorie)
    if bautyp:    sql+=" AND bautyp=?";    params.append(bautyp)
    if baubar is not None: sql+=" AND baubar=?"; params.append(int(baubar))
    sql += " ORDER BY id"
    cur.execute(sql, params); rows = cur.fetchall(); conn.close()
    results = [fmt_gebaeude(r) for r in rows]
    if terrain:
        out = []
        for g in results:
            for ts in g["terrain_effektivitaet"].values():
                if terrain in ts: out.append(g); break
        return out
    return results

@app.get("/gebaeude/{gebaeude_id}")
async def get_gebaeude(gebaeude_id: int):
    conn = get_db(); cur = conn.cursor()
    cur.execute("SELECT * FROM gebaeude_typen WHERE id=?", (gebaeude_id,))
    row = cur.fetchone(); conn.close()
    if not row: raise HTTPException(404, "Gebäude nicht gefunden")
    return fmt_gebaeude(row)

# ─── Endpoints: Provinz-Feldtypen ─────────────────────────────────────────────
@app.get("/provinz/feldtypen")
async def get_feldtypen():
    conn = get_db(); cur = conn.cursor()
    cur.execute("SELECT * FROM provinz_feldtypen ORDER BY id")
    rows = cur.fetchall(); conn.close()
    return [{"id":r["id"],"name":r["name"],"beschreibung":r["beschreibung"],
             "groesse_px":r["groesse_px"],"ist_baubar":bool(r["ist_baubar"]),
             "bautypen":safe_json(r["bautypen"],[]),"farbe_leer":r["farbe_leer"]} for r in rows]

@app.get("/provinz/feldtypen/{feldtyp_id}")
async def get_feldtyp(feldtyp_id: str):
    conn = get_db(); cur = conn.cursor()
    cur.execute("SELECT * FROM provinz_feldtypen WHERE id=?", (feldtyp_id,))
    row = cur.fetchone()
    if not row: conn.close(); raise HTTPException(404, "Feldtyp nicht gefunden")
    bautypen = safe_json(row["bautypen"], [])
    baubare = []
    for bt in bautypen:
        cur.execute("SELECT * FROM gebaeude_typen WHERE bautyp=? AND baubar=1 ORDER BY tech_level,id",(bt,))
        baubare.extend([fmt_gebaeude(r) for r in cur.fetchall()])
    conn.close()
    return {"id":row["id"],"name":row["name"],"beschreibung":row["beschreibung"],
            "groesse_px":row["groesse_px"],"ist_baubar":bool(row["ist_baubar"]),
            "bautypen":bautypen,"farbe_leer":row["farbe_leer"],"baubare_gebaeude":baubare}

# ─── Endpoints: Ressourcen ────────────────────────────────────────────────────
@app.get("/ressourcen/typen")
async def get_ressourcen_typen():
    conn = get_db(); cur = conn.cursor()
    cur.execute("SELECT DISTINCT typ, COUNT(*) as anzahl FROM ressourcen GROUP BY typ ORDER BY typ")
    rows = cur.fetchall(); conn.close()
    return [{"typ":r["typ"],"anzahl":r["anzahl"]} for r in rows]

@app.get("/ressourcen")
async def get_ressourcen(typ: Optional[str]=None, name: Optional[str]=None):
    conn = get_db(); cur = conn.cursor()
    sql = "SELECT * FROM ressourcen WHERE 1=1"; params = []
    if typ:  sql+=" AND typ=?";       params.append(typ)
    if name: sql+=" AND name LIKE ?"; params.append(f"%{name}%")
    sql += " ORDER BY typ,name"
    cur.execute(sql, params); rows = cur.fetchall(); conn.close()
    return [fmt_ressource(r) for r in rows]

@app.get("/ressourcen/{ressource_id}")
async def get_ressource(ressource_id: int):
    conn = get_db(); cur = conn.cursor()
    cur.execute("SELECT * FROM ressourcen WHERE id=?", (ressource_id,))
    row = cur.fetchone(); conn.close()
    if not row: raise HTTPException(404, "Ressource nicht gefunden")
    return fmt_ressource(row)

# ─── Endpoints: Vorkommen ─────────────────────────────────────────────────────
@app.get("/vorkommen/typen")
async def get_vorkommen_typen():
    conn = get_db(); cur = conn.cursor()
    cur.execute("SELECT DISTINCT typ, COUNT(*) as anzahl FROM vorkommen GROUP BY typ ORDER BY typ")
    rows = cur.fetchall(); conn.close()
    return [{"typ":r["typ"],"anzahl":r["anzahl"]} for r in rows]

@app.get("/vorkommen")
async def get_vorkommen(typ: Optional[str]=None, name: Optional[str]=None):
    conn = get_db(); cur = conn.cursor()
    sql = "SELECT * FROM vorkommen WHERE 1=1"; params = []
    if typ:  sql+=" AND typ=?";       params.append(typ)
    if name: sql+=" AND name LIKE ?"; params.append(f"%{name}%")
    sql += " ORDER BY tech,name"
    cur.execute(sql, params); rows = cur.fetchall(); conn.close()
    return [fmt_vorkommen(r) for r in rows]

@app.get("/vorkommen/{vorkommen_id}")
async def get_vorkommen_by_id(vorkommen_id: int):
    conn = get_db(); cur = conn.cursor()
    cur.execute("SELECT * FROM vorkommen WHERE id=?", (vorkommen_id,))
    row = cur.fetchone(); conn.close()
    if not row: raise HTTPException(404, "Vorkommen nicht gefunden")
    return fmt_vorkommen(row)

# ─── Static Files (NACH makedirs + init_db!) ──────────────────────────────────
app.mount("/css",      StaticFiles(directory="css"),      name="css")
app.mount("/js",       StaticFiles(directory="js"),       name="js")
app.mount("/terrains", StaticFiles(directory="terrains"), name="terrains")

# HTML Pages
@app.get("/login.html")
async def login_page():
    return FileResponse("login.html")

@app.get("/admin.html")
async def admin_page():
    return FileResponse("admin.html")

@app.get("/index.html")
async def index_page():
    return FileResponse("index.html")

if __name__ == "__main__":
    import uvicorn
    print("🚀 Verbrannte Zone Backend v2.1.0")
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8000,
        ssl_keyfile="key.pem",
        ssl_certfile="cert.pem"
    )

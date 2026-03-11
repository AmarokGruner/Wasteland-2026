from fastapi import FastAPI, HTTPException, Request
from pydantic import BaseModel
from typing import List, Optional, Any, Union, Dict
import sqlite3
import os
import uvicorn
import json
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import RedirectResponse, FileResponse
import datetime
from datetime import timedelta, timezone
from jose import JWTError, jwt
import bcrypt

# Passlib/Bcrypt 4.0+ Compatibility Patch for Python 3.13
if not hasattr(bcrypt, "__about__"):
    bcrypt.__about__ = type('about', (object,), {'__version__': getattr(bcrypt, '__version__', '4.0.0')})

DB_PATH = "verbrannte_zone.db"

def get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def row_to_dict(row):
    return dict(row)

app = FastAPI(title="Verbrannte Zone API")

app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

# --- Static file serving ---
@app.get("/")
async def read_root():
    """Einstiegspunkt: Liefert die index.html aus, 
    das JS im Frontend kümmert sich um den Auth-Redirect zu login.html"""
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

# ──────────────────────────────────────────────
# AUTH (JWT & Hashing)
# ──────────────────────────────────────────────
SECRET_KEY = "wasteland_ultra_secure_secret_2026" # In Production aus Env laden!
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 120
REFRESH_TOKEN_EXPIRE_DAYS = 7

def verify_password(plain_password, hashed_password):
    try:
        if isinstance(plain_password, str):
            plain_password = plain_password.encode('utf-8')
        if isinstance(hashed_password, str):
            hashed_password = hashed_password.encode('utf-8')
        return bcrypt.checkpw(plain_password, hashed_password)
    except Exception:
        return False

def get_password_hash(password):
    if isinstance(password, str):
        password = password.encode('utf-8')
    return bcrypt.hashpw(password, bcrypt.gensalt()).decode('utf-8')

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.datetime.now(datetime.timezone.utc) + expires_delta
    else:
        expire = datetime.datetime.now(datetime.timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire, "type": "access"})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

def create_refresh_token(data: dict):
    expire = datetime.datetime.now(datetime.timezone.utc) + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
    to_encode = data.copy()
    to_encode.update({"exp": expire, "type": "refresh"})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

def get_token_user(token: str):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        if payload.get("type") != "access":
            return None
        username: str = payload.get("sub")
        if username is None:
            return None
    except JWTError:
        return None
    
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT * FROM users WHERE username=?", (username,))
    row = cur.fetchone()
    conn.close()
    return dict(row) if row else None

def require_admin(token: str):
    user = get_token_user(token)
    if not user or user["role"] != "admin":
        raise HTTPException(status_code=403, detail="Nicht autorisiert")
    return user

def log_admin_action(conn, admin_id: int, action: str, target_type: str = None, target_id: str = None, payload: dict = None):
    cur = conn.cursor()
    cur.execute(
        "INSERT INTO admin_logs (admin_id, action, target_type, target_id, payload) VALUES (?, ?, ?, ?, ?)",
        (admin_id, action, target_type, target_id, json.dumps(payload or {}))
    )
    conn.commit()

# ──────────────────────────────────────────────
# AUTH ENDPOINTS
# ──────────────────────────────────────────────
class LoginRequest(BaseModel):
    username: str
    password: str

class RegisterRequest(BaseModel):
    username: str
    password: str
    email: Optional[str] = None

class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    role: str
    username: str
    player_id: Optional[int]

class RefreshRequest(BaseModel):
    refresh_token: str

@app.post("/auth/register", response_model=TokenResponse)
def register(req: RegisterRequest):
    conn = get_connection()
    cur = conn.cursor()
    
    # Check if user exists
    cur.execute("SELECT id FROM users WHERE username=?", (req.username,))
    if cur.fetchone():
        conn.close()
        raise HTTPException(status_code=400, detail="Benutzername bereits vergeben")
    
    # Create user
    pw_hash = get_password_hash(req.password)
    cur.execute(
        "INSERT INTO users (username, email, password_hash) VALUES (?, ?, ?)",
        (req.username, req.email, pw_hash)
    )
    user_id = cur.lastrowid
    
    # Create empty player profile
    cur.execute("INSERT INTO players (name) VALUES (?)", (req.username,))
    player_id = cur.lastrowid
    cur.execute("UPDATE users SET player_id=? WHERE id=?", (player_id, user_id))
    
    conn.commit()
    
    access_token = create_access_token(data={"sub": req.username})
    refresh_token = create_refresh_token(data={"sub": req.username})
    
    conn.close()
    return {
        "access_token": access_token, 
        "refresh_token": refresh_token, 
        "role": "player", 
        "username": req.username, 
        "player_id": player_id
    }

class ForgotPasswordRequest(BaseModel):
    username: str

class ResetPasswordRequest(BaseModel):
    token: str
    new_password: str

@app.post("/auth/login", response_model=TokenResponse)
def login(req: LoginRequest):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT * FROM users WHERE username=?", (req.username,))
    user = cur.fetchone()
    if not user or not verify_password(req.password, user["password_hash"]):
        conn.close()
        raise HTTPException(status_code=401, detail="Ungültige Anmeldedaten")
    
    # Check if banned
    if user["role"] == "banned":
        conn.close()
        raise HTTPException(status_code=403, detail="Account gesperrt")
        
    # Update last login
    cur.execute("UPDATE users SET last_login=CURRENT_TIMESTAMP WHERE id=?", (user["id"],))
    conn.commit()
    conn.close()
    
    access_token = create_access_token(data={"sub": user["username"]})
    refresh_token = create_refresh_token(data={"sub": user["username"]})
    
    return {
        "access_token": access_token, 
        "refresh_token": refresh_token, 
        "role": user["role"], 
        "username": user["username"], 
        "player_id": user["player_id"]
    }

@app.post("/auth/refresh", response_model=TokenResponse)
def refresh(req: RefreshRequest):
    try:
        payload = jwt.decode(req.refresh_token, SECRET_KEY, algorithms=[ALGORITHM])
        if payload.get("type") != "refresh":
             raise HTTPException(status_code=401, detail="Ungültiger Refresh-Token")
        username: str = payload.get("sub")
    except JWTError:
        raise HTTPException(status_code=401, detail="JWT Error")
    
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT * FROM users WHERE username=?", (username,))
    user = cur.fetchone()
    conn.close()
    
    if not user:
        raise HTTPException(status_code=401, detail="Benutzer nicht gefunden")
    
    access_token = create_access_token(data={"sub": user["username"]})
    refresh_token = create_refresh_token(data={"sub": user["username"]})
    
    return {
        "access_token": access_token, 
        "refresh_token": refresh_token, 
        "role": user["role"], 
        "username": user["username"], 
        "player_id": user["player_id"]
    }

@app.post("/auth/logout")
def logout():
    return {"ok": True}

@app.post("/auth/forgot-password")
def forgot_password(req: ForgotPasswordRequest):
    import secrets
    token = secrets.token_urlsafe(32)
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(
        "UPDATE users SET reset_token=?, reset_token_expires=? WHERE username=?",
        (token, (datetime.now(timezone.utc) + timedelta(hours=1)).isoformat(), req.username)
    )
    conn.commit()
    conn.close()
    # In reality, send email. Here, we'll just log it.
    print(f"DEBUG: Password reset token for {req.username}: {token}")
    return {"ok": True, "message": "Falls der Account existiert, wurde ein Reset-Token generiert."}

@app.post("/auth/reset-password")
def reset_password(req: ResetPasswordRequest):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT * FROM users WHERE reset_token=?", (req.token,))
    user = cur.fetchone()
    if not user:
        conn.close()
        raise HTTPException(status_code=400, detail="Ungültiger Token")
    
    expires = datetime.fromisoformat(user["reset_token_expires"])
    if datetime.now(timezone.utc) > expires.replace(tzinfo=timezone.utc):
        conn.close()
        raise HTTPException(status_code=400, detail="Token abgelaufen")
    
    pw_hash = get_password_hash(req.new_password)
    cur.execute(
        "UPDATE users SET password_hash=?, reset_token=NULL, reset_token_expires=NULL WHERE id=?",
        (pw_hash, user["id"])
    )
    conn.commit()
    conn.close()
    return {"ok": True}
def me(token: str):
    user = get_token_user(token)
    if not user:
        raise HTTPException(status_code=401, detail="Nicht angemeldet")
    return {"id": user["id"], "username": user["username"], "role": user["role"], "player_id": user.get("player_id")}

# ──────────────────────────────────────────────
# ADMIN: USERS
# ──────────────────────────────────────────────
class UserCreate(BaseModel):
    username: str
    password: str
    role: str = "player"
    player_id: Optional[int] = None

@app.get("/admin/users")
def admin_list_users(token: str):
    require_admin(token)
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        SELECT u.id, u.username, u.email, u.role, u.player_id, u.created_at, u.last_login,
               p.name as player_name
        FROM users u LEFT JOIN players p ON u.player_id = p.id ORDER BY u.id
    """)
    rows = [row_to_dict(r) for r in cur.fetchall()]
    conn.close()
    return rows

@app.post("/admin/users")
def admin_create_user(token: str, req: UserCreate):
    admin_user = require_admin(token)
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("INSERT INTO users(username, password_hash, role, player_id) VALUES (?,?,?,?)",
                (req.username, get_password_hash(req.password), req.role, req.player_id))
    new_id = cur.lastrowid
    log_admin_action(conn, admin_user["id"], "create_user", "user", str(new_id), {"username": req.username, "role": req.role})
    conn.commit()
    conn.close()
    return {"ok": True}

@app.get("/admin/log")
def admin_get_logs(token: str, limit: int = 100):
    require_admin(token)
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        SELECT l.*, u.username as admin_name 
        FROM admin_logs l 
        LEFT JOIN users u ON l.admin_id = u.id 
        ORDER BY l.timestamp DESC LIMIT ?
    """, (limit,))
    rows = [row_to_dict(r) for r in cur.fetchall()]
    conn.close()
    return rows

# ──────────────────────────────────────────────
# ADMIN: GEBÄUDE (gebaeude_typen)
# ──────────────────────────────────────────────
class BuildingUpdate(BaseModel):
    name: Optional[str] = None
    kategorie: Optional[str] = None
    baukosten_mips: Optional[int] = None
    arbeiter: Optional[int] = None
    wohnraum: Optional[int] = None
    lagerkapazitaet: Optional[int] = None
    produktion: Optional[str] = None
    rohstoffverbrauch: Optional[str] = None
    terrain_effektivitaet: Optional[str] = None

class BuildingCreate(BuildingUpdate):
    name: str

# --- Spiel-Modelle ---
class PlaceBuildingRequest(BaseModel):
    building_type: str
    x: int
    y: int

class UpgradeBuildingRequest(BaseModel):
    building_x: int
    building_y: int

class ClaimProvinceRequest(BaseModel):
    world_x: int
    world_y: int
    name: str
    terrain: str

class TransportRequest(BaseModel):
    nach_provinz_id: int
    ressource_id: int
    menge: int

@app.get("/admin/buildings")
def admin_list_buildings(token: str):
    require_admin(token)
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT * FROM gebaeude_typen ORDER BY id")
    rows = [row_to_dict(r) for r in cur.fetchall()]
    conn.close()
    return rows

@app.get("/admin/buildings/{bid}")
def admin_get_building(bid: int, token: str):
    require_admin(token)
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT * FROM gebaeude_typen WHERE id=?", (bid,))
    row = cur.fetchone()
    conn.close()
    if not row:
        raise HTTPException(status_code=404, detail="Nicht gefunden")
    return row_to_dict(row)

@app.post("/admin/buildings")
def admin_create_building(token: str, req: BuildingCreate):
    require_admin(token)
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""INSERT INTO gebaeude_typen(name,kategorie,baukosten_mips,arbeiter,wohnraum,lagerkapazitaet,produktion,rohstoffverbrauch,terrain_effektivitaet)
                   VALUES(?,?,?,?,?,?,?,?,?)""",
                (req.name, req.kategorie, req.baukosten_mips or 0, req.arbeiter or 0,
                 req.wohnraum or 0, req.lagerkapazitaet or 0,
                 req.produktion or '[]', req.rohstoffverbrauch or '[]',
                 req.terrain_effektivitaet or '{}'))
    conn.commit()
    bid = cur.lastrowid
    conn.close()
    return admin_get_building(bid, token)

@app.put("/admin/buildings/{bid}")
def admin_update_building(bid: int, token: str, req: BuildingUpdate):
    require_admin(token)
    conn = get_connection()
    cur = conn.cursor()
    fields, vals = [], []
    for f, v in req.model_dump(exclude_none=True).items():
        fields.append(f"{f}=?")
        vals.append(v)
    if not fields:
        conn.close()
        return {"ok": True}
    vals.append(bid)
    cur.execute(f"UPDATE gebaeude_typen SET {','.join(fields)},updated_at=CURRENT_TIMESTAMP WHERE id=?", vals)
    conn.commit()
    conn.close()
    return admin_get_building(bid, token)

@app.delete("/admin/buildings/{bid}")
def admin_delete_building(bid: int, token: str):
    require_admin(token)
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("DELETE FROM gebaeude_typen WHERE id=?", (bid,))
    conn.commit()
    conn.close()
    return {"ok": True}

# ──────────────────────────────────────────────
# ADMIN: RESSOURCEN
# ──────────────────────────────────────────────
class RessourceUpdate(BaseModel):
    name: Optional[str] = None
    typ: Optional[str] = None
    produktionswert: Optional[int] = None
    platz_land: Optional[int] = None
    platz_wasser: Optional[int] = None
    platz_luft: Optional[int] = None
    verbrauch_pro_1000: Optional[float] = None
    beschreibung: Optional[str] = None

class RessourceCreate(RessourceUpdate):
    name: str

@app.get("/admin/ressourcen")
def admin_list_ressourcen(token: str):
    require_admin(token)
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT * FROM ressourcen ORDER BY id")
    rows = [row_to_dict(r) for r in cur.fetchall()]
    conn.close()
    return rows

@app.get("/admin/ressourcen/{rid}")
def admin_get_ressource(rid: int, token: str):
    require_admin(token)
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT * FROM ressourcen WHERE id=?", (rid,))
    row = cur.fetchone()
    conn.close()
    if not row:
        raise HTTPException(status_code=404, detail="Nicht gefunden")
    return row_to_dict(row)

@app.post("/admin/ressourcen")
def admin_create_ressource(token: str, req: RessourceCreate):
    require_admin(token)
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""INSERT INTO ressourcen(name,typ,produktionswert,platz_land,platz_wasser,platz_luft,beschreibung)
                   VALUES(?,?,?,?,?,?,?)""",
                (req.name, req.typ, req.produktionswert or 0,
                 req.platz_land or 1, req.platz_wasser or 1, req.platz_luft or 1,
                 req.beschreibung or ''))
    conn.commit()
    rid = cur.lastrowid
    conn.close()
    return admin_get_ressource(rid, token)

@app.put("/admin/ressourcen/{rid}")
def admin_update_ressource(rid: int, token: str, req: RessourceUpdate):
    require_admin(token)
    conn = get_connection()
    cur = conn.cursor()
    fields, vals = [], []
    for f, v in req.model_dump(exclude_none=True).items():
        fields.append(f"{f}=?")
        vals.append(v)
    if not fields:
        conn.close()
        return {"ok": True}
    vals.append(rid)
    cur.execute(f"UPDATE ressourcen SET {','.join(fields)},updated_at=CURRENT_TIMESTAMP WHERE id=?", vals)
    conn.commit()
    conn.close()
    return admin_get_ressource(rid, token)

@app.delete("/admin/ressourcen/{rid}")
def admin_delete_ressource(rid: int, token: str):
    require_admin(token)
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("DELETE FROM ressourcen WHERE id=?", (rid,))
    conn.commit()
    conn.close()
    return {"ok": True}

# ──────────────────────────────────────────────
# ADMIN: VORKOMMEN
# ──────────────────────────────────────────────
class VorkommenUpdate(BaseModel):
    name: Optional[str] = None
    typ: Optional[str] = None
    tech: Optional[int] = None
    suchkosten: Optional[int] = None
    beschreibung: Optional[str] = None
    findwahrscheinlichkeit: Optional[str] = None

class VorkommenCreate(VorkommenUpdate):
    name: str

@app.get("/admin/vorkommen")
def admin_list_vorkommen(token: str):
    require_admin(token)
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT * FROM vorkommen ORDER BY id")
    rows = [row_to_dict(r) for r in cur.fetchall()]
    conn.close()
    return rows

@app.get("/admin/vorkommen/{vid}")
def admin_get_vorkommen(vid: int, token: str):
    require_admin(token)
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT * FROM vorkommen WHERE id=?", (vid,))
    row = cur.fetchone()
    conn.close()
    if not row:
        raise HTTPException(status_code=404, detail="Nicht gefunden")
    return row_to_dict(row)

@app.post("/admin/vorkommen")
def admin_create_vorkommen(token: str, req: VorkommenCreate):
    require_admin(token)
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("INSERT INTO vorkommen(name,typ,tech,suchkosten,beschreibung,findwahrscheinlichkeit) VALUES(?,?,?,?,?,?)",
                (req.name, req.typ, req.tech or 0, req.suchkosten or 0, req.beschreibung or '', req.findwahrscheinlichkeit or '{}'))
    conn.commit()
    vid = cur.lastrowid
    conn.close()
    return admin_get_vorkommen(vid, token)

@app.put("/admin/vorkommen/{vid}")
def admin_update_vorkommen(vid: int, token: str, req: VorkommenUpdate):
    require_admin(token)
    conn = get_connection()
    cur = conn.cursor()
    fields, vals = [], []
    for f, v in req.model_dump(exclude_none=True).items():
        fields.append(f"{f}=?")
        vals.append(v)
    if not fields:
        conn.close()
        return {"ok": True}
    vals.append(vid)
    cur.execute(f"UPDATE vorkommen SET {','.join(fields)},updated_at=CURRENT_TIMESTAMP WHERE id=?", vals)
    conn.commit()
    conn.close()
    return admin_get_vorkommen(vid, token)

@app.delete("/admin/vorkommen/{vid}")
def admin_delete_vorkommen(vid: int, token: str):
    require_admin(token)
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("DELETE FROM vorkommen WHERE id=?", (vid,))
    conn.commit()
    conn.close()
    return {"ok": True}

# ──────────────────────────────────────────────
# ADMIN: REGIERUNGSFORMEN
# ──────────────────────────────────────────────
class RegierungsformUpdate(BaseModel):
    name: Optional[str] = None
    formtyp: Optional[str] = None
    techlevel: Optional[int] = None
    ausbauwert_regierungssitz: Optional[int] = None
    kulturverbreitung: Optional[float] = None
    grundmoral: Optional[int] = None
    forschungsfortschritt: Optional[float] = None
    produktivitaet: Optional[float] = None
    wachstum: Optional[float] = None
    finanzen: Optional[float] = None
    sicherheit: Optional[float] = None
    moralmalus_armee_aussen: Optional[int] = None
    entfernungsmalus: Optional[float] = None
    lebensmittelbedarf: Optional[float] = None
    verbrauchsgutbedarf: Optional[float] = None
    streikbereitschaft: Optional[float] = None
    auswanderbereitschaft: Optional[float] = None
    milizen: Optional[float] = None
    fremdkultur_verlust: Optional[int] = None
    aufstand: Optional[int] = None
    krieg_moeglich: Optional[int] = None
    provinzanzahl_bis_malus: Optional[int] = None
    malus_beschreibung: Optional[str] = None
    beschreibung: Optional[str] = None
    boni: Optional[str] = None
    voraussetzungen: Optional[str] = None

class RegierungsformCreate(RegierungsformUpdate):
    name: str

@app.get("/admin/regierungsformen")
def admin_list_regierungsformen(token: str):
    require_admin(token)
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT * FROM regierungsformen ORDER BY id")
    rows = [row_to_dict(r) for r in cur.fetchall()]
    conn.close()
    return rows

@app.get("/admin/regierungsformen/{rid}")
def admin_get_regierungsform(rid: int, token: str):
    require_admin(token)
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT * FROM regierungsformen WHERE id=?", (rid,))
    row = cur.fetchone()
    conn.close()
    if not row:
        raise HTTPException(status_code=404, detail="Nicht gefunden")
    return row_to_dict(row)

@app.post("/admin/regierungsformen")
def admin_create_regierungsform(token: str, req: RegierungsformCreate):
    require_admin(token)
    conn = get_connection()
    cur = conn.cursor()
    # Wir nutzen hier eine dynamische Erstellung wie im Update, um alle Felder zu unterstützen
    data = req.model_dump(exclude_none=True)
    if "name" not in data:
        conn.close()
        raise HTTPException(status_code=400, detail="Name ist erforderlich")
    
    cols = list(data.keys())
    placeholders = ["?"] * len(cols)
    cur.execute(f"INSERT INTO regierungsformen({','.join(cols)}) VALUES({','.join(placeholders)})",
                list(data.values()))
    conn.commit()
    rid = cur.lastrowid
    conn.close()
    return admin_get_regierungsform(rid, token)

@app.put("/admin/regierungsformen/{rid}")
def admin_update_regierungsform(rid: int, token: str, req: RegierungsformUpdate):
    require_admin(token)
    conn = get_connection()
    cur = conn.cursor()
    fields, vals = [], []
    for f, v in req.model_dump(exclude_none=True).items():
        fields.append(f"{f}=?")
        vals.append(v)
    if not fields:
        conn.close()
        return {"ok": True}
    vals.append(rid)
    cur.execute(f"UPDATE regierungsformen SET {','.join(fields)},updated_at=CURRENT_TIMESTAMP WHERE id=?", vals)
    conn.commit()
    conn.close()
    return admin_get_regierungsform(rid, token)

@app.delete("/admin/regierungsformen/{rid}")
def admin_delete_regierungsform(rid: int, token: str):
    require_admin(token)
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("DELETE FROM regierungsformen WHERE id=?", (rid,))
    conn.commit()
    conn.close()
    return {"ok": True}

# ──────────────────────────────────────────────
# ADMIN: TERRAIN (world_terrain)
# ──────────────────────────────────────────────
class TerrainUpdate(BaseModel):
    name: Optional[str] = None
    startgebiet: Optional[int] = None
    regen_pct: Optional[int] = None
    aufwertungen: Optional[str] = None
    abwertungen: Optional[str] = None
    beschreibung: Optional[str] = None
    bild_url: Optional[str] = None
    gebaeude_effektivitaet: Optional[str] = None
    color: Optional[str] = None
    icon: Optional[str] = None
    playable: Optional[int] = None

class TerrainCreate(TerrainUpdate):
    id: str
    name: str

@app.get("/admin/terrain")
def admin_list_terrain(token: str):
    require_admin(token)
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT * FROM terrain_typen ORDER BY name")
    rows = [row_to_dict(r) for r in cur.fetchall()]
    conn.close()
    return rows

@app.get("/admin/terrain/{tid}")
def admin_get_terrain(tid: str, token: str):
    require_admin(token)
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT * FROM terrain_typen WHERE id=?", (tid,))
    row = cur.fetchone()
    conn.close()
    if not row:
        raise HTTPException(status_code=404, detail="Nicht gefunden")
    return row_to_dict(row)

@app.put("/admin/terrain/{tid}")
def admin_update_terrain(tid: str, token: str, req: TerrainUpdate):
    require_admin(token)
    conn = get_connection()
    cur = conn.cursor()
    fields, vals = [], []
    for f, v in req.model_dump(exclude_none=True).items():
        fields.append(f"{f}=?")
        vals.append(v)
    if not fields:
        conn.close()
        return {"ok": True}
    vals.append(tid)
    cur.execute(f"UPDATE terrain_typen SET {','.join(fields)} WHERE id=?", vals)
    conn.commit()
    conn.close()
    return admin_get_terrain(tid, token)

@app.delete("/admin/terrain/{tid}")
def admin_delete_terrain(tid: str, token: str):
    require_admin(token)
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("DELETE FROM terrain_typen WHERE id=?", (tid,))
    conn.commit()
    conn.close()
    return {"ok": True}

# ──────────────────────────────────────────────
# ADMIN: GEBÄUDE-FELDER (provinz_feldtypen)
# ──────────────────────────────────────────────
class FeldtypUpdate(BaseModel):
    name: Optional[str] = None
    beschreibung: Optional[str] = None
    groesse_px: Optional[int] = None
    ist_baubar: Optional[int] = None
    bautypen: Optional[str] = None
    farbe_leer: Optional[str] = None

class FeldtypCreate(FeldtypUpdate):
    id: str
    name: str

@app.get("/admin/gebaeude_felder")
def admin_list_feldtypen(token: str):
    require_admin(token)
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT * FROM provinz_feldtypen ORDER BY id")
    rows = [row_to_dict(r) for r in cur.fetchall()]
    conn.close()
    return rows

@app.get("/admin/gebaeude_felder/{fid}")
def admin_get_feldtyp(fid: str, token: str):
    require_admin(token)
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT * FROM provinz_feldtypen WHERE id=?", (fid,))
    row = cur.fetchone()
    conn.close()
    if not row:
        raise HTTPException(status_code=404, detail="Nicht gefunden")
    return row_to_dict(row)

@app.put("/admin/gebaeude_felder/{fid}")
def admin_update_feldtyp(fid: str, token: str, req: FeldtypUpdate):
    require_admin(token)
    conn = get_connection()
    cur = conn.cursor()
    fields, vals = [], []
    for f, v in req.model_dump(exclude_none=True).items():
        fields.append(f"{f}=?")
        vals.append(v)
    if not fields:
        conn.close()
        return {"ok": True}
    vals.append(fid)
    cur.execute(f"UPDATE provinz_feldtypen SET {','.join(fields)} WHERE id=?", vals)
    conn.commit()
    conn.close()
    return admin_get_feldtyp(fid, token)

@app.delete("/admin/gebaeude_felder/{fid}")
def admin_delete_feldtyp(fid: str, token: str):
    require_admin(token)
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("DELETE FROM provinz_feldtypen WHERE id=?", (fid,))
    conn.commit()
    conn.close()
    return {"ok": True}

# ──────────────────────────────────────────────
# ADMIN: ARTIKEL
# ──────────────────────────────────────────────
class ArtikelUpdate(BaseModel):
    name: Optional[str] = None
    spezies: Optional[str] = None
    einheittext: Optional[str] = None
    modultyp: Optional[str] = None
    zugehoerig: Optional[str] = None
    bautyp: Optional[str] = None
    produktionspunkte: Optional[int] = None
    rohstoffbedarf: Optional[Union[str, List, Dict]] = None
    modulgroesse: Optional[int] = None
    auswirkung_einheitenwerte: Optional[Union[str, Dict]] = None
    transportkapazitaet: Optional[Union[str, Dict]] = None
    platzbedarf: Optional[Union[str, Dict]] = None
    beschreibung: Optional[str] = None
    kategorie: Optional[str] = None
    preis_mips: Optional[int] = None
    preis_muenzen: Optional[int] = None
    gewicht: Optional[int] = None
    haltbarkeit: Optional[int] = None

class ArtikelCreate(ArtikelUpdate):
    name: str

@app.get("/admin/artikel")
def admin_list_artikel(token: str):
    require_admin(token)
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT * FROM artikel ORDER BY id")
    rows = [row_to_dict(r) for r in cur.fetchall()]
    conn.close()
    return rows

@app.get("/admin/artikel/{aid}")
def admin_get_artikel(aid: int, token: str):
    require_admin(token)
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT * FROM artikel WHERE id=?", (aid,))
    row = cur.fetchone()
    conn.close()
    if not row:
        raise HTTPException(status_code=404, detail="Nicht gefunden")
    return row_to_dict(row)

@app.post("/admin/artikel")
def admin_create_artikel(token: str, req: ArtikelCreate):
    require_admin(token)
    conn = get_connection()
    cur = conn.cursor()
    data = req.model_dump()
    # JSON-Felder serialisieren
    for f in ["rohstoffbedarf", "auswirkung_einheitenwerte", "transportkapazitaet", "platzbedarf"]:
        if data.get(f) is not None and not isinstance(data[f], str):
            data[f] = json.dumps(data[f], ensure_ascii=False)
        elif data.get(f) is None:
            if f == "rohstoffbedarf": data[f] = "[]"
            else: data[f] = "{}"
            
    cols = list(data.keys())
    placeholders = ",".join(["?"] * len(cols))
    cur.execute(f"INSERT INTO artikel({','.join(cols)}) VALUES({placeholders})", list(data.values()))
    conn.commit()
    aid = cur.lastrowid
    conn.close()
    return admin_get_artikel(aid, token)

@app.put("/admin/artikel/{aid}")
def admin_update_artikel(aid: int, token: str, req: ArtikelUpdate):
    require_admin(token)
    conn = get_connection()
    cur = conn.cursor()
    fields, vals = [], []
    for f, v in req.model_dump(exclude_none=True).items():
        if f in ["rohstoffbedarf", "auswirkung_einheitenwerte", "transportkapazitaet", "platzbedarf"] and not isinstance(v, str):
            v = json.dumps(v, ensure_ascii=False)
        fields.append(f"{f}=?")
        vals.append(v)
    if not fields:
        conn.close()
        return {"ok": True}
    vals.append(aid)
    cur.execute(f"UPDATE artikel SET {','.join(fields)},updated_at=CURRENT_TIMESTAMP WHERE id=?", vals)
    conn.commit()
    conn.close()
    return admin_get_artikel(aid, token)

@app.delete("/admin/artikel/{aid}")
def admin_delete_artikel(aid: int, token: str):
    require_admin(token)
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("DELETE FROM artikel WHERE id=?", (aid,))
    conn.commit()
    conn.close()
    return {"ok": True}

# ──────────────────────────────────────────────
# ADMIN: EINHEITEN (einheiten_typen)
# ──────────────────────────────────────────────
class EinheitUpdate(BaseModel):
    name: Optional[str] = None
    spezies: Optional[str] = None
    einheitenklasse: Optional[str] = None
    zugehoerig: Optional[str] = None
    fortbewegung: Optional[str] = None
    erstellbedingung: Optional[str] = None
    max_reichweite: Optional[str] = None
    geschwindigkeit: Optional[float] = None
    nahkampf_staerke: Optional[int] = None
    nahkampf_panzerung: Optional[int] = None
    fernkampf_panzerung: Optional[int] = None
    einheitengroesse: Optional[int] = None
    transport_land: Optional[int] = None
    platzbedarf_see: Optional[int] = None
    platzbedarf_untersee: Optional[int] = None
    platzbedarf_luft: Optional[int] = None
    module: Optional[str] = None
    beschreibung: Optional[str] = None

class EinheitCreate(EinheitUpdate):
    name: str

@app.get("/admin/einheiten")
def admin_list_einheiten(token: str):
    require_admin(token)
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT * FROM einheiten_typen ORDER BY id")
    rows = [row_to_dict(r) for r in cur.fetchall()]
    conn.close()
    return rows

@app.get("/admin/einheiten/{eid}")
def admin_get_einheit(eid: int, token: str):
    require_admin(token)
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT * FROM einheiten_typen WHERE id=?", (eid,))
    row = cur.fetchone()
    conn.close()
    if not row:
        raise HTTPException(status_code=404, detail="Nicht gefunden")
    return row_to_dict(row)

@app.post("/admin/einheiten")
def admin_create_einheit(token: str, req: EinheitCreate):
    require_admin(token)
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""INSERT INTO einheiten_typen(name, spezies, einheitenklasse, zugehoerig, fortbewegung, erstellbedingung, max_reichweite, geschwindigkeit, nahkampf_staerke, nahkampf_panzerung, fernkampf_panzerung, einheitengroesse, transport_land, platzbedarf_see, platzbedarf_untersee, platzbedarf_luft, module, beschreibung)
                   VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
                (req.name, req.spezies or '', req.einheitenklasse or '', req.zugehoerig or '', req.fortbewegung or 'Boden', req.erstellbedingung or 'keine', req.max_reichweite or 'Nahkampf', req.geschwindigkeit or 1.0, req.nahkampf_staerke or 0, req.nahkampf_panzerung or 0, req.fernkampf_panzerung or 0, req.einheitengroesse or 1, req.transport_land or 0, req.platzbedarf_see or 0, req.platzbedarf_untersee or 0, req.platzbedarf_luft or 0, req.module or '[]', req.beschreibung or ''))
    conn.commit()
    eid = cur.lastrowid
    conn.close()
    return admin_get_einheit(eid, token)

@app.put("/admin/einheiten/{eid}")
def admin_update_einheit(eid: int, token: str, req: EinheitUpdate):
    require_admin(token)
    conn = get_connection()
    cur = conn.cursor()
    fields, vals = [], []
    for f, v in req.model_dump(exclude_none=True).items():
        fields.append(f"{f}=?")
        vals.append(v)
    if not fields:
        conn.close()
        return {"ok": True}
    vals.append(eid)
    cur.execute(f"UPDATE einheiten_typen SET {','.join(fields)},updated_at=CURRENT_TIMESTAMP WHERE id=?", vals)
    conn.commit()
    conn.close()
    return admin_get_einheit(eid, token)

@app.delete("/admin/einheiten/{eid}")
def admin_delete_einheit(eid: int, token: str):
    require_admin(token)
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("DELETE FROM einheiten_typen WHERE id=?", (eid,))
    conn.commit()
    conn.close()
    return {"ok": True}

# ──────────────────────────────────────────────
# ADMIN: LEBEWESEN
# ──────────────────────────────────────────────
class LebewesenUpdate(BaseModel):
    name: Optional[str] = None
    typ: Optional[str] = None
    staerke: Optional[int] = None
    gesundheit: Optional[int] = None
    bevoelkerung_kosten: Optional[int] = None
    beschreibung: Optional[str] = None

class LebewesenCreate(LebewesenUpdate):
    name: str

@app.get("/admin/lebewesen")
def admin_list_lebewesen(token: str):
    require_admin(token)
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT * FROM lebewesen ORDER BY id")
    rows = [row_to_dict(r) for r in cur.fetchall()]
    conn.close()
    return rows

@app.get("/admin/lebewesen/{lid}")
def admin_get_lebewesen(lid: int, token: str):
    require_admin(token)
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT * FROM lebewesen WHERE id=?", (lid,))
    row = cur.fetchone()
    conn.close()
    if not row:
        raise HTTPException(status_code=404, detail="Nicht gefunden")
    return row_to_dict(row)

@app.post("/admin/lebewesen")
def admin_create_lebewesen(token: str, req: LebewesenCreate):
    require_admin(token)
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("INSERT INTO lebewesen(name,typ,staerke,gesundheit,bevoelkerung_kosten,beschreibung) VALUES(?,?,?,?,?,?)",
                (req.name, req.typ or '', req.staerke or 0,
                 req.gesundheit or 0, req.bevoelkerung_kosten or 0, req.beschreibung or ''))
    conn.commit()
    lid = cur.lastrowid
    conn.close()
    return admin_get_lebewesen(lid, token)

@app.put("/admin/lebewesen/{lid}")
def admin_update_lebewesen(lid: int, token: str, req: LebewesenUpdate):
    require_admin(token)
    conn = get_connection()
    cur = conn.cursor()
    fields, vals = [], []
    for f, v in req.model_dump(exclude_none=True).items():
        fields.append(f"{f}=?")
        vals.append(v)
    if not fields:
        conn.close()
        return {"ok": True}
    vals.append(lid)
    cur.execute(f"UPDATE lebewesen SET {','.join(fields)},updated_at=CURRENT_TIMESTAMP WHERE id=?", vals)
    conn.commit()
    conn.close()
    return admin_get_lebewesen(lid, token)

@app.delete("/admin/lebewesen/{lid}")
def admin_delete_lebewesen(lid: int, token: str):
    require_admin(token)
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("DELETE FROM lebewesen WHERE id=?", (lid,))
    conn.commit()
    conn.close()
    return {"ok": True}

# ──────────────────────────────────────────────
# SPIELER + PROVINZEN (Basis-Endpunkte)
# ──────────────────────────────────────────────
@app.get("/player/{player_id}")
def get_player(player_id: int, token: str):
    user = get_token_user(token)
    if not user:
        raise HTTPException(status_code=401, detail="Nicht angemeldet")
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT * FROM players WHERE id=?", (player_id,))
    row = cur.fetchone()
    conn.close()
    if not row:
        raise HTTPException(status_code=404, detail="Spieler nicht gefunden")
    return row_to_dict(row)

@app.get("/player/{player_id}/provinzen")
def get_provinzen(player_id: int, token: str):
    user = get_token_user(token)
    if not user:
        raise HTTPException(status_code=401, detail="Nicht angemeldet")
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT * FROM provinzen WHERE player_id=?", (player_id,))
    rows = [row_to_dict(r) for r in cur.fetchall()]
    conn.close()
    return {"provinzen": rows, "player_id": player_id}

@app.get("/player/{player_id}/provinzen/{prov_id}")
def get_provinz_detail(player_id: int, prov_id: int, token: str):
    user = get_token_user(token)
    if not user:
        raise HTTPException(status_code=401, detail="Nicht angemeldet")
    conn = get_connection()
    cur = conn.cursor()
    
    # Provinz-Basisdaten
    cur.execute("SELECT * FROM provinzen WHERE id=? AND player_id=?", (prov_id, player_id))
    prov = cur.fetchone()
    if not prov:
        conn.close()
        raise HTTPException(status_code=404, detail="Provinz nicht gefunden")
    
    # Gebäude
    cur.execute("""
        SELECT pg.*, gt.name as building_type 
        FROM provinz_gebaeude pg
        JOIN gebaeude_typen gt ON pg.gebaeude_typ_id = gt.id
        WHERE pg.provinz_id=?
    """, (prov_id,))
    buildings = [row_to_dict(r) for r in cur.fetchall()]
    
    # Vorkommen
    cur.execute("""
        SELECT pv.*, v.name, v.typ 
        FROM provinz_vorkommen pv
        JOIN vorkommen v ON pv.vorkommen_id = v.id
        WHERE pv.provinz_id=?
    """, (prov_id,))
    vorkommen = [row_to_dict(r) for r in cur.fetchall()]
    
    conn.close()
    res = row_to_dict(prov)
    res["buildings"] = buildings
    res["vorkommen"] = vorkommen
    return res

@app.get("/player/{player_id}/provinzen/{prov_id}/lager")
def get_provinz_lager(player_id: int, prov_id: int, token: str):
    user = get_token_user(token)
    if not user:
        raise HTTPException(status_code=401, detail="Nicht angemeldet")
    conn = get_connection()
    cur = conn.cursor()
    
    # Sicherstellen, dass die Provinz dem Spieler gehört
    cur.execute("SELECT id FROM provinzen WHERE id=? AND player_id=?", (prov_id, player_id))
    if not cur.fetchone():
        conn.close()
        raise HTTPException(status_code=404, detail="Provinz nicht gefunden")
        
    cur.execute("""
        SELECT pl.*, r.name as ressource_name, r.typ
        FROM provinz_lager pl
        JOIN ressourcen r ON pl.ressource_id = r.id
        WHERE pl.provinz_id=? AND pl.menge > 0
    """, (prov_id,))
    eintraege = [row_to_dict(r) for r in cur.fetchall()]
    
    # Kapazität berechnen (Summe aller Lagergebäude)
    cur.execute("""
        SELECT SUM(gt.lagerkapazitaet * pg.stufe) as kap
        FROM provinz_gebaeude pg
        JOIN gebaeude_typen gt ON pg.gebaeude_typ_id = gt.id
        WHERE pg.provinz_id=?
    """, (prov_id,))
    kap_row = cur.fetchone()
    kap = kap_row[0] if kap_row[0] else 1000 # Fallback 1000
    
    conn.close()
    return {
        "provinz_id": prov_id,
        "eintraege": eintraege,
        "kapazitaet": kap,
        "anzahl_positionen": len(eintraege)
    }

@app.post("/player/{player_id}/provinzen")
def claim_province(player_id: int, token: str, req: ClaimProvinceRequest):
    user = get_token_user(token)
    if not user:
        raise HTTPException(status_code=401, detail="Nicht angemeldet")
    
    conn = get_connection()
    cur = conn.cursor()
    
    # Prüfen ob bereits besetzt
    cur.execute("SELECT id FROM provinzen WHERE world_x=? AND world_y=?", (req.world_x, req.world_y))
    if cur.fetchone():
        conn.close()
        raise HTTPException(status_code=400, detail="Diese Provinz ist bereits besetzt!")
        
    cur.execute("""
        INSERT INTO provinzen (player_id, name, world_x, world_y, terrain)
        VALUES (?, ?, ?, ?, ?)
    """, (player_id, req.name, req.world_x, req.world_y, req.terrain))
    prov_id = cur.lastrowid
    conn.commit()
    conn.close()
    return {"ok": True, "provinz": {"id": prov_id}}

@app.post("/player/{player_id}/provinzen/{prov_id}/build")
def build_building(player_id: int, prov_id: int, token: str, req: PlaceBuildingRequest):
    user = get_token_user(token)
    if not user:
        raise HTTPException(status_code=401, detail="Nicht angemeldet")
        
    conn = get_connection()
    cur = conn.cursor()
    
    # Gebäudetyp finden
    cur.execute("SELECT * FROM gebaeude_typen WHERE name=?", (req.building_type,))
    typ = cur.fetchone()
    if not typ:
        conn.close()
        raise HTTPException(status_code=404, detail="Gebäudetyp nicht gefunden")
    
    # Prüfen ob Feld frei
    cur.execute("SELECT id FROM provinz_gebaeude WHERE provinz_id=? AND x=? AND y=?", (prov_id, req.x, req.y))
    if cur.fetchone():
        conn.close()
        raise HTTPException(status_code=400, detail="Feld ist bereits belegt")
        
    # TODO: Kosten prüfen & abziehen
    
    cur.execute("""
        INSERT INTO provinz_gebaeude (provinz_id, gebaeude_typ_id, x, y, stufe)
        VALUES (?, ?, ?, ?, 1)
    """, (prov_id, typ["id"], req.x, req.y))
    
    conn.commit()
    conn.close()
    return {"ok": True}

@app.post("/player/{player_id}/provinzen/{prov_id}/upgrade")
def upgrade_building(player_id: int, prov_id: int, token: str, req: UpgradeBuildingRequest):
    user = get_token_user(token)
    if not user:
        raise HTTPException(status_code=401, detail="Nicht angemeldet")
        
    conn = get_connection()
    cur = conn.cursor()
    
    cur.execute("""
        UPDATE provinz_gebaeude SET stufe = stufe + 1
        WHERE provinz_id=? AND x=? AND y=?
    """, (prov_id, req.building_x, req.building_y))
    
    if cur.rowcount == 0:
        conn.close()
        raise HTTPException(status_code=404, detail="Gebäude nicht gefunden")
        
    conn.commit()
    conn.close()
    return {"ok": True}

@app.get("/player/{player_id}/credit")
def get_player_credit(player_id: int, token: str):
    user = get_token_user(token)
    if not user:
        raise HTTPException(status_code=401, detail="Nicht angemeldet")
    # Simulation: Immer 240h Guthaben
    return {"credit_hours": 240}

@app.post("/player/{player_id}/resources/produce")
def produce_resources(player_id: int, token: str, hours: int = 1, preview_only: bool = False):
    user = get_token_user(token)
    if not user:
        raise HTTPException(status_code=401, detail="Nicht angemeldet")
        
    # Basis-Ressourcen Produktion (sehr einfach für den Moment)
    # TODO: Echte Logik basierend auf Gebäuden implementieren
    
    if preview_only:
        # Dummy Bericht
        conn = get_connection()
        cur = conn.cursor()
        cur.execute("SELECT id FROM provinzen WHERE player_id=?", (player_id,))
        prov_ids = [r[0] for r in cur.fetchall()]
        conn.close()
        
        bericht = []
        for pid in prov_ids:
            bericht.append({
                "provinz_id": pid,
                "stats": {"wohnraum": 100, "bevoelkerung": 50, "bedarf": 30},
                "effizienz": 1.0,
                "deltas": {"1": hours * 10}, # 1 = Eisen ID?
                "neues_lager": {"1": 100 + (hours * 10)}
            })
        return {"bericht": bericht}
    
    return {"ok": True, "message": f"{hours}h Produktion berechnet."}

@app.post("/player/{player_id}/provinzen/{prov_id}/transport")
def send_transport(player_id: int, prov_id: int, token: str, req: TransportRequest):
    user = get_token_user(token)
    if not user:
        raise HTTPException(status_code=401, detail="Nicht angemeldet")
    
    conn = get_connection()
    cur = conn.cursor()
    
    # 1. Check Source Lager
    cur.execute("SELECT menge FROM provinz_lager WHERE provinz_id=? AND ressource_id=?", (prov_id, req.ressource_id))
    row = cur.fetchone()
    if not row or row["menge"] < req.menge:
        conn.close()
        raise HTTPException(status_code=400, detail="Nicht genügend Ressourcen im Lager!")
    
    # 2. Update Source
    cur.execute("UPDATE provinz_lager SET menge = menge - ? WHERE provinz_id=? AND ressource_id=?", (req.menge, prov_id, req.ressource_id))
    
    # 3. Update Target
    cur.execute("SELECT id FROM provinz_lager WHERE provinz_id=? AND ressource_id=?", (req.nach_provinz_id, req.ressource_id))
    if cur.fetchone():
        cur.execute("UPDATE provinz_lager SET menge = menge + ? WHERE provinz_id=? AND ressource_id=?", (req.menge, req.nach_provinz_id, req.ressource_id))
    else:
        cur.execute("INSERT INTO provinz_lager (provinz_id, ressource_id, menge) VALUES (?, ?, ?)", (req.nach_provinz_id, req.ressource_id, req.menge))
        
    conn.commit()
    conn.close()
    return {"ok": True, "message": "Transport erfolgreich gesendet."}

@app.get("/player/{player_id}/resources/total")
def get_player_resources(player_id: int, token: str):
    user = get_token_user(token)
    if not user:
        raise HTTPException(status_code=401, detail="Nicht angemeldet")
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        SELECT r.name, SUM(pl.menge) as gesamt
        FROM provinz_lager pl
        JOIN ressourcen r ON pl.ressource_id = r.id
        JOIN provinzen p ON pl.provinz_id = p.id
        WHERE p.player_id=?
        GROUP BY r.name ORDER BY r.name
    """, (player_id,))
    rows = [{"name": r["name"], "menge": r["gesamt"]} for r in cur.fetchall()]
    conn.close()
    return rows

# ──────────────────────────────────────────────
# WORLD MAP & TERRAINS
# ──────────────────────────────────────────────

@app.get("/terrains")
def get_public_terrains():
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT * FROM terrain_typen ORDER BY name")
    rows = [row_to_dict(r) for r in cur.fetchall()]
    conn.close()
    
    for r in rows:
        name_lower = r["name"].lower().replace("ä", "ae").replace("ö", "oe").replace("ü", "ue").replace(" ", "_")
        r["gif_filename"] = f"terrain_{name_lower}.gif"
        
        for field in ["aufwertungen", "abwertungen", "gebaeude_effektivitaet"]:
            if r.get(field):
                try:
                    r[field] = json.loads(r[field])
                except Exception:
                    r[field] = [] if field.endswith("ngen") else {}
    return rows

@app.get("/world/map")
def get_public_world_map():
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        SELECT w.x, w.y, t.name as terrain_name, w.owner_id
        FROM world_map_cells w
        LEFT JOIN terrain_typen t ON w.terrain_id = t.id
        ORDER BY w.y, w.x
    """)
    rows = cur.fetchall()
    conn.close()
    
    if not rows:
        return {"size": 50, "cells": []}
        
    grid = [["Ozean" for _ in range(50)] for _ in range(50)]
    for r in rows:
        grid[r["y"]][r["x"]] = r["terrain_name"] or "Ozean"
        
    return {"size": 50, "cells": grid}

@app.get("/world/map/full")
def get_admin_world_map(token: str):
    require_admin(token)
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        SELECT w.x, w.y, w.terrain_id, w.owner_id, w.is_ruin_province, w.has_ocean_border,
               t.name as terrain_name, t.color as terrain_color,
               p.name as owner_name
        FROM world_map_cells w
        LEFT JOIN terrain_typen t ON w.terrain_id = t.id
        LEFT JOIN players p ON w.owner_id = p.id
        ORDER BY w.y, w.x
    """)
    rows = [row_to_dict(r) for r in cur.fetchall()]
    conn.close()
    return {"size": 50, "cells": rows}

class WorldMapCellUpdate(BaseModel):
    x: int
    y: int
    terrain_id: int

class WorldMapBulkUpdate(BaseModel):
    cells: List[WorldMapCellUpdate]

class ImportStaticRequest(BaseModel):
    map_data: List[List[str]]

def recalc_ocean_borders_fast(cur):
    cur.execute("SELECT id FROM terrain_typen WHERE name='Ozean'")
    row = cur.fetchone()
    if not row: return
    ocean_id = row[0]
    
    cur.execute("UPDATE world_map_cells SET has_ocean_border = 0")
    cur.execute("""
        UPDATE world_map_cells SET has_ocean_border = 1
        WHERE EXISTS (
            SELECT 1 FROM world_map_cells o 
            WHERE o.terrain_id = ? 
            AND (
                (o.x = world_map_cells.x - 1 AND o.y = world_map_cells.y) OR
                (o.x = world_map_cells.x + 1 AND o.y = world_map_cells.y) OR
                (o.x = world_map_cells.x AND o.y = world_map_cells.y - 1) OR
                (o.x = world_map_cells.x AND o.y = world_map_cells.y + 1)
            )
        )
    """, (ocean_id,))

@app.patch("/admin/world/map/cell")
def admin_update_map_cell(token: str, req: WorldMapCellUpdate):
    require_admin(token)
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("UPDATE world_map_cells SET terrain_id=? WHERE x=? AND y=?", (req.terrain_id, req.x, req.y))
    recalc_ocean_borders_fast(cur)
    conn.commit()
    conn.close()
    return {"ok": True}

@app.post("/admin/world/map/cells/bulk")
def admin_update_map_cells_bulk(token: str, req: WorldMapBulkUpdate):
    require_admin(token)
    conn = get_connection()
    cur = conn.cursor()
    for cell in req.cells:
        cur.execute("UPDATE world_map_cells SET terrain_id=? WHERE x=? AND y=?", (cell.terrain_id, cell.x, cell.y))
    recalc_ocean_borders_fast(cur)
    conn.commit()
    conn.close()
    return {"ok": True, "updated": len(req.cells)}

@app.post("/admin/world/import-static")
def admin_import_static_map(token: str, req: ImportStaticRequest):
    require_admin(token)
    conn = get_connection()
    cur = conn.cursor()
    
    cur.execute("SELECT id, name FROM terrain_typen")
    terrains = {row["name"]: row["id"] for row in cur.fetchall()}
    terrains_lower = {k.lower(): v for k, v in terrains.items()}
    fallback_ocean_id = terrains.get("Ozean", 1)
    
    imported = 0
    for y, row in enumerate(req.map_data):
        for x, cell_name in enumerate(row):
            t_name = str(cell_name).strip()
            if t_name.lower() == "player":
                tid = terrains_lower.get("startposition") or terrains_lower.get("grasland", fallback_ocean_id)
            else:
                tid = terrains.get(t_name)
                if not tid:
                    tid = terrains_lower.get(t_name.lower())
                if not tid:
                    tid = terrains_lower.get("grasland", fallback_ocean_id)
            
            cur.execute("INSERT OR IGNORE INTO world_map_cells (x, y, terrain_id) VALUES (?, ?, ?)", (x, y, tid))
            imported += 1
            
    recalc_ocean_borders_fast(cur)
    conn.commit()
    conn.close()
    return {"ok": True, "imported": imported}

# ──────────────────────────────────────────────
# ADMIN WORLD GENERATION / CELL EDITING
# ──────────────────────────────────────────────
import random

class WorldGenerateRequest(BaseModel):
    width: int = 50
    height: int = 50
    seed: Optional[int] = None

@app.post("/admin/world/generate")
def admin_generate_world(token: str, req: WorldGenerateRequest):
    admin_user = require_admin(token)
    if req.width < 10 or req.width > 200 or req.height < 10 or req.height > 200:
        raise HTTPException(status_code=400, detail="Ungültige Abmessungen (10-200)")
        
    if req.seed is not None:
        random.seed(req.seed)
        
    conn = get_connection()
    cur = conn.cursor()
    
    cur.execute("SELECT id, name FROM terrain_typen")
    terrains = {row["name"].lower(): row["id"] for row in cur.fetchall()}
    
    ozean_id = terrains.get("ozean", 1)
    gras_id = terrains.get("grasland", 2)
    wueste_id = terrains.get("wüste", 3)
    oeland_id = terrains.get("ödland", 4)
    gebirge_id = terrains.get("gebirge", 5)
    wald_id = terrains.get("wald", 6)
    
    land_choices = [gras_id]*3 + [wueste_id]*2 + [oeland_id]*2 + [gebirge_id]*2 + [wald_id]*2
    
    cur.execute("DELETE FROM world_map_cells")
    
    cells = []
    
    for y in range(req.height):
        for x in range(req.width):
            if x == 0 or x == req.width - 1 or y == 0 or y == req.height - 1:
                tid = ozean_id
            else:
                tid = random.choice(land_choices)
                
            cells.append((x, y, tid))
            
    cur.executemany("INSERT INTO world_map_cells (x, y, terrain_id) VALUES (?, ?, ?)", cells)
    
    recalc_ocean_borders_fast(cur)
    
    log_admin_action(conn, admin_user["id"], "generate_world", "world", None, {"width": req.width, "height": req.height, "seed": req.seed})
    
    conn.commit()
    conn.close()
    return {"ok": True, "generated_cells": len(cells)}

class SetRuinRequest(BaseModel):
    is_ruin: bool
    preset_buildings: List[str] = []

@app.post("/admin/world/province/{x}/{y}/ruins")
def admin_set_province_ruin(x: int, y: int, token: str, req: SetRuinRequest):
    admin_user = require_admin(token)
    conn = get_connection()
    cur = conn.cursor()
    
    preset_json = json.dumps(req.preset_buildings)
    cur.execute("UPDATE world_map_cells SET is_ruin_province=?, preset_buildings=? WHERE x=? AND y=?", 
                (int(req.is_ruin), preset_json, x, y))
                
    if cur.rowcount == 0:
        conn.close()
        raise HTTPException(status_code=404, detail="Zelle nicht gefunden")
        
    log_admin_action(conn, admin_user["id"], "set_ruin", "world_map_cells", f"{x},{y}", {"is_ruin": req.is_ruin, "presets": req.preset_buildings})
    conn.commit()
    conn.close()
    return {"ok": True}
    
class AssignOwnerRequest(BaseModel):
    player_id: Optional[int]

@app.post("/admin/world/province/{x}/{y}/assign-owner")
def admin_assign_owner(x: int, y: int, token: str, req: AssignOwnerRequest):
    admin_user = require_admin(token)
    conn = get_connection()
    cur = conn.cursor()
    
    cur.execute("UPDATE world_map_cells SET owner_id=? WHERE x=? AND y=?", (req.player_id, x, y))
    
    if cur.rowcount == 0:
        conn.close()
        raise HTTPException(status_code=404, detail="Zelle nicht gefunden")
        
    log_admin_action(conn, admin_user["id"], "assign_owner", "world_map_cells", f"{x},{y}", {"player_id": req.player_id})
    conn.commit()
    conn.close()
    return {"ok": True}

# ──────────────────────────────────────────────
# ADMIN PLAYER / PROVINCE OVERRIDES
# ──────────────────────────────────────────────
import datetime

@app.post("/admin/player/{player_id}/reset")
def admin_reset_player(player_id: int, token: str):
    admin_user = require_admin(token)
    conn = get_connection()
    cur = conn.cursor()
    
    cur.execute("SELECT last_reset_at FROM players WHERE id=?", (player_id,))
    row = cur.fetchone()
    if not row:
        conn.close()
        raise HTTPException(status_code=404, detail="Spieler nicht gefunden")
        
    last_reset = row["last_reset_at"]
    if last_reset:
        try:
            last_dt = datetime.datetime.fromisoformat(last_reset)
            if (datetime.datetime.now() - last_dt).total_seconds() < 86400:
                conn.close()
                raise HTTPException(status_code=400, detail="Account kann nur einmal alle 24 Stunden zurückgesetzt werden.")
        except:
            pass
            
    try:
        cur.execute("UPDATE players SET has_bunker=0, mips=0, tech_level=0, last_reset_at=CURRENT_TIMESTAMP WHERE id=?", (player_id,))
    except sqlite3.OperationalError:
        # Fallback if columns don't exist
        cur.execute("UPDATE players SET last_reset_at=CURRENT_TIMESTAMP WHERE id=?", (player_id,))
    
    cur.execute("UPDATE world_map_cells SET owner_id=NULL WHERE owner_id=?", (player_id,))
    cur.execute("DELETE FROM provinz_lager WHERE player_id=?", (player_id,))
    
    log_admin_action(conn, admin_user["id"], "reset_player", "player", str(player_id))
    conn.commit()
    conn.close()
    return {"ok": True}

class TechRequest(BaseModel):
    tech_level: int

@app.post("/admin/player/{player_id}/tech")
def admin_set_player_tech(player_id: int, token: str, req: TechRequest):
    admin_user = require_admin(token)
    conn = get_connection()
    cur = conn.cursor()
    try:
        cur.execute("UPDATE players SET tech_level=? WHERE id=?", (req.tech_level, player_id))
        if cur.rowcount == 0:
            conn.close()
            raise HTTPException(status_code=404, detail="Spieler nicht gefunden")
    except sqlite3.OperationalError:
        pass
        
    log_admin_action(conn, admin_user["id"], "set_tech", "player", str(player_id), {"tech_level": req.tech_level})
    conn.commit()
    conn.close()
    return {"ok": True}

class MipsRequest(BaseModel):
    amount: float
    province_id: Optional[int] = None

@app.post("/admin/player/{player_id}/mips")
def admin_give_player_mips(player_id: int, token: str, req: MipsRequest):
    admin_user = require_admin(token)
    conn = get_connection()
    cur = conn.cursor()
    try:
        cur.execute("UPDATE players SET mips = mips + ? WHERE id=?", (req.amount, player_id))
        if cur.rowcount == 0:
            conn.close()
            raise HTTPException(status_code=404, detail="Spieler nicht gefunden")
    except sqlite3.OperationalError:
        pass
        
    log_admin_action(conn, admin_user["id"], "give_mips", "player", str(player_id), {"amount": req.amount, "province_id": req.province_id})
    conn.commit()
    conn.close()
    return {"ok": True}

class ForceBuildRequest(BaseModel):
    template_id: int
    field_id: int

@app.post("/admin/province/{x}/{y}/build")
def admin_force_build(x: int, y: int, token: str, req: ForceBuildRequest):
    admin_user = require_admin(token)
    conn = get_connection()
    
    log_admin_action(conn, admin_user["id"], "force_build", "province", f"{x},{y}", {"template_id": req.template_id, "field_id": req.field_id})
    conn.commit()
    conn.close()
    return {"ok": True}

class ForceEventRequest(BaseModel):
    type: str
    payload: dict

@app.post("/admin/province/{x}/{y}/event")
def admin_force_event(x: int, y: int, token: str, req: ForceEventRequest):
    admin_user = require_admin(token)
    conn = get_connection()
    log_admin_action(conn, admin_user["id"], "force_event", "province", f"{x},{y}", {"type": req.type, "payload": req.payload})
    conn.commit()
    conn.close()
    return {"ok": True}

# ──────────────────────────────────────────────
# ONBOARDING & SPAWN
# ──────────────────────────────────────────────

# Startressourcen: (ressource_id, menge)
STARTRESSOURCEN = [
    (18, 500),   # Getreide
    (2,  500),   # Wasser
    (67, 200),   # Bauholz
    (4,  100),   # Stein
]

def assign_start_province(player_id: int, conn):
    """
    Sucht eine freie Startgelände-Zelle, weist sie dem Spieler zu,
    legt eine Provinz an, befüllt das Lager mit Startressourcen
    und platziert den Bunker auf Feld (15,15).
    Gibt { world_x, world_y, provinz_id } zurück.
    """
    cur = conn.cursor()

    # 1. Alle Startgelände-Terrain-IDs ermitteln
    cur.execute("SELECT id FROM terrain_typen WHERE startgebiet = 1")
    start_terrain_ids = [r[0] for r in cur.fetchall()]
    if not start_terrain_ids:
        raise HTTPException(status_code=500, detail="Keine Startgelände in der Datenbank definiert!")

    placeholders = ",".join("?" * len(start_terrain_ids))

    # 2. Alle besetzten Zellen (owner_id IS NOT NULL) für Mindestabstand
    cur.execute("SELECT x, y FROM world_map_cells WHERE owner_id IS NOT NULL")
    occupied = [(r[0], r[1]) for r in cur.fetchall()]

    # 3. Freie Startzellen laden
    cur.execute(
        f"SELECT x, y FROM world_map_cells WHERE terrain_id IN ({placeholders}) AND owner_id IS NULL",
        start_terrain_ids
    )
    candidates = [(r[0], r[1]) for r in cur.fetchall()]
    if not candidates:
        raise HTTPException(status_code=503, detail="Keine freien Startfelder verfügbar!")

    # 4. Zelle mit Mindestabstand 5 bevorzugen
    MIN_DIST = 5
    def min_dist(cx, cy):
        if not occupied:
            return 999
        return min(abs(cx - ox) + abs(cy - oy) for ox, oy in occupied)

    good = [c for c in candidates if min_dist(*c) >= MIN_DIST]
    chosen = (good or candidates)[0]  # Fallback auf nächstbeste
    wx, wy = chosen

    # 5. Zelle dem Spieler zuweisen
    cur.execute("UPDATE world_map_cells SET owner_id=? WHERE x=? AND y=?", (player_id, wx, wy))

    # Terrain-Name für Provinz ermitteln
    cur.execute("""
        SELECT t.name FROM world_map_cells wmc
        JOIN terrain_typen t ON wmc.terrain_id = t.id
        WHERE wmc.x=? AND wmc.y=?
    """, (wx, wy))
    terrain_row = cur.fetchone()
    terrain_name = terrain_row[0] if terrain_row else "Grasland"

    # 6. Provinz anlegen
    cur.execute("""
        INSERT INTO provinzen (player_id, world_x, world_y, name, terrain)
        VALUES (?, ?, ?, ?, ?)
    """, (player_id, wx, wy, f"Startprovinz ({wx},{wy})", terrain_name))
    prov_id = cur.lastrowid

    # 7. Startressourcen ins Lager legen
    for res_id, menge in STARTRESSOURCEN:
        # Nur eintragen wenn Ressource in DB vorhanden
        cur.execute("SELECT id FROM ressourcen WHERE id=?", (res_id,))
        if cur.fetchone():
            cur.execute("""
                INSERT INTO provinz_lager (provinz_id, ressource_id, menge)
                VALUES (?, ?, ?)
                ON CONFLICT (provinz_id, ressource_id) DO UPDATE SET menge = menge + excluded.menge
            """, (prov_id, res_id, menge))

    # 8. Startgebäude (Bunker, id=1) auf Feld (15,15)
    cur.execute("SELECT id FROM gebaeude_typen WHERE id=1")
    if cur.fetchone():
        cur.execute("""
            INSERT OR IGNORE INTO provinz_gebaeude (provinz_id, gebaeude_typ_id, x, y, stufe)
            VALUES (?, 1, 15, 15, 1)
        """, (prov_id,))

    # 9. spawn_count hochzählen
    cur.execute("UPDATE players SET spawn_count = spawn_count + 1 WHERE id=?", (player_id,))

    return {"world_x": wx, "world_y": wy, "provinz_id": prov_id}


@app.post("/player/{player_id}/spawn")
def spawn_start_province(player_id: int, token: str):
    """Weist dem Spieler automatisch seine erste Startprovinz zu."""
    user = get_token_user(token)
    if not user:
        raise HTTPException(status_code=401, detail="Nicht angemeldet")

    conn = get_connection()
    cur = conn.cursor()

    # Missbrauchsschutz: Nur 1 Spawn erlaubt
    try:
        cur.execute("SELECT spawn_count FROM players WHERE id=?", (player_id,))
        row = cur.fetchone()
        if not row:
            conn.close()
            raise HTTPException(status_code=404, detail="Spieler nicht gefunden")
        if row["spawn_count"] and row["spawn_count"] >= 1:
            conn.close()
            raise HTTPException(status_code=400, detail="Startprovinz wurde bereits generiert. Nutze 'Neu anfangen' (Account-Reset).")
    except sqlite3.OperationalError:
        pass  # Spalte existiert noch nicht → Migration wurde nicht ausgeführt

    try:
        result = assign_start_province(player_id, conn)

        # Tutorial-Schritt auf 0 setzen
        try:
            cur.execute("UPDATE users SET tutorial_step=0 WHERE player_id=?", (player_id,))
        except sqlite3.OperationalError:
            pass  # Spalte existiert noch nicht

        conn.commit()
        conn.close()
        return {"ok": True, **result}
    except HTTPException:
        conn.rollback()
        conn.close()
        raise
    except Exception as e:
        conn.rollback()
        conn.close()
        raise HTTPException(status_code=500, detail=f"Spawn fehlgeschlagen: {str(e)}")


@app.get("/player/{player_id}/tutorial")
def get_tutorial_step(player_id: int, token: str):
    """Gibt den aktuellen Tutorial-Schritt des Spielers zurück."""
    user = get_token_user(token)
    if not user:
        raise HTTPException(status_code=401, detail="Nicht angemeldet")
    conn = get_connection()
    cur = conn.cursor()
    try:
        cur.execute("SELECT tutorial_step FROM users WHERE player_id=?", (player_id,))
        row = cur.fetchone()
    except sqlite3.OperationalError:
        row = None
    conn.close()
    step = row["tutorial_step"] if row and row["tutorial_step"] is not None else -1
    return {"tutorial_step": step}


@app.post("/player/{player_id}/tutorial/advance")
def advance_tutorial(player_id: int, token: str):
    """Setzt den Tutorial-Schritt um 1 vor."""
    user = get_token_user(token)
    if not user:
        raise HTTPException(status_code=401, detail="Nicht angemeldet")
    conn = get_connection()
    cur = conn.cursor()
    try:
        cur.execute(
            "UPDATE users SET tutorial_step = tutorial_step + 1 WHERE player_id=?",
            (player_id,)
        )
        cur.execute("SELECT tutorial_step FROM users WHERE player_id=?", (player_id,))
        row = cur.fetchone()
        conn.commit()
        conn.close()
        step = row["tutorial_step"] if row else 99
        return {"ok": True, "tutorial_step": step}
    except sqlite3.OperationalError:
        conn.close()
        return {"ok": True, "tutorial_step": 99}


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)

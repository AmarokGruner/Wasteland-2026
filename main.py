from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List, Optional, Any, Union, Dict
import sqlite3
import os
import uvicorn
import json
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import RedirectResponse, FileResponse

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
# AUTH (simple token from localStorage)
# ──────────────────────────────────────────────
import hashlib

SECRET_KEY = "wasteland_secret_2024"

def hash_password(pw: str) -> str:
    return hashlib.sha256(pw.encode()).hexdigest()

def get_token_user(token: str):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT * FROM users WHERE token=?", (token,))
    row = cur.fetchone()
    conn.close()
    return dict(row) if row else None

def require_admin(token: str):
    user = get_token_user(token)
    if not user or user["role"] != "admin":
        raise HTTPException(status_code=403, detail="Nicht autorisiert")
    return user

# ──────────────────────────────────────────────
# AUTH ENDPOINTS
# ──────────────────────────────────────────────
class LoginRequest(BaseModel):
    username: str
    password: str

class LogoutRequest(BaseModel):
    token: str

@app.post("/auth/login")
def login(req: LoginRequest):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT * FROM users WHERE username=?", (req.username,))
    user = cur.fetchone()
    if not user or user["password_hash"] != hash_password(req.password):
        conn.close()
        raise HTTPException(status_code=401, detail="Ungültige Anmeldedaten")
    token = hashlib.sha256(f"{user['id']}{SECRET_KEY}{req.username}".encode()).hexdigest()
    cur.execute("UPDATE users SET token=? WHERE id=?", (token, user["id"]))
    conn.commit()
    conn.close()
    user_dict = dict(user)
    return {"token": token, "role": user_dict["role"], "username": user_dict["username"], "player_id": user_dict.get("player_id")}

@app.post("/auth/logout")
def logout(req: LogoutRequest):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("UPDATE users SET token=NULL WHERE token=?", (req.token,))
    conn.commit()
    conn.close()
    return {"ok": True}

@app.get("/auth/me")
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
        SELECT u.id, u.username, u.role, u.player_id, u.created_at,
               p.name as player_name
        FROM users u LEFT JOIN players p ON u.player_id = p.id ORDER BY u.id
    """)
    rows = [row_to_dict(r) for r in cur.fetchall()]
    conn.close()
    return rows

@app.post("/admin/users")
def admin_create_user(token: str, req: UserCreate):
    require_admin(token)
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("INSERT INTO users(username, password_hash, role, player_id) VALUES (?,?,?,?)",
                (req.username, hash_password(req.password), req.role, req.player_id))
    conn.commit()
    conn.close()
    return {"ok": True}

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
if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)

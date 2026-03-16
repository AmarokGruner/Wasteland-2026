from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from app.models import get_db, Player, Province, User
from app.api.admin.users import require_admin, log_admin_action
from pydantic import BaseModel
from typing import List, Optional

router = APIRouter(prefix="/admin", tags=["Admin-Players"])

class PlayerStats(BaseModel):
    id: int
    name: str
    last_login: Optional[str]
    provinces: int
    tech_level: int
    regierungsform: str

@router.get("/players", response_model=List[PlayerStats])
def get_admin_players(token: str, db: Session = Depends(get_db)):
    require_admin(token)
    
    # We need to join Player and User for last_login
    # Assuming there's a User model. Let's check if User is in models.py
    # If not, we'll use raw query
    conn = db.get_bind().raw_connection()
    cur = conn.cursor()
    cur.execute("""
        SELECT p.id, p.name, u.last_login, 
               (SELECT COUNT(*) FROM provinzen WHERE player_id = p.id),
               p.tech_level, r.name
        FROM players p
        LEFT JOIN users u ON u.player_id = p.id
        LEFT JOIN regierungsformen r ON p.regierungsform_id = r.id
    """)
    rows = cur.fetchall()
    cur.close()
    
    result = []
    for r in rows:
        result.append({
            "id": r[0],
            "name": r[1],
            "last_login": r[2],
            "provinces": r[3],
            "tech_level": r[4],
            "regierungsform": r[5] or "Unbekannt"
        })
    return result

class SetStatsRequest(BaseModel):
    moral: Optional[int] = None
    gesundheit: Optional[int] = None

@router.post("/province/{id}/set")
def admin_set_province_stats(id: int, req: SetStatsRequest, token: str, db: Session = Depends(get_db)):
    admin = require_admin(token)
    prov = db.query(Province).filter(Province.id == id).first()
    if not prov:
        raise HTTPException(status_code=404, detail="Provinz nicht gefunden")
    
    if req.moral is not None:
        prov.moral = max(0, min(100, req.moral))
    if req.gesundheit is not None:
        prov.gesundheit = max(0, min(100, req.gesundheit))
    
    db.commit()
    log_admin_action(0, "set_province_stats", "province", str(id), req.dict())
    return {"success": True}

class AddMipsRequest(BaseModel):
    amount: float

@router.post("/province/{id}/mips")
def admin_add_mips(id: int, req: AddMipsRequest, token: str, db: Session = Depends(get_db)):
    admin = require_admin(token)
    prov = db.query(Province).filter(Province.id == id).first()
    if not prov:
        raise HTTPException(status_code=404, detail="Provinz nicht gefunden")
    
    prov.mips += req.amount
    db.commit()
    log_admin_action(0, "add_mips", "province", str(id), req.dict())
    return {"success": True}

class AddLagerRequest(BaseModel):
    resource_id: int
    amount: float

@router.post("/province/{id}/lager")
def admin_add_lager(id: int, req: AddLagerRequest, token: str, db: Session = Depends(get_db)):
    admin = require_admin(token)
    # This needs the ProvinceLager model
    from app.models import ProvinceLager
    item = db.query(ProvinceLager).filter(ProvinceLager.provinz_id == id, ProvinceLager.ressource_id == req.resource_id).first()
    if not item:
        item = ProvinceLager(provinz_id=id, ressource_id=req.resource_id, menge=0)
        db.add(item)
    
    item.menge += req.amount
    db.commit()
    log_admin_action(0, "add_lager", "province", str(id), req.dict())
    return {"success": True}

class SetTechRequest(BaseModel):
    tech_level: int

@router.post("/player/{id}/tech")
def admin_set_tech(id: int, req: SetTechRequest, token: str, db: Session = Depends(get_db)):
    admin = require_admin(token)
    player = db.query(Player).filter(Player.id == id).first()
    if not player:
        raise HTTPException(status_code=404, detail="Spieler nicht gefunden")
    
    player.tech_level = req.tech_level
    db.commit()
    log_admin_action(0, "set_tech", "player", str(id), req.dict())
    return {"success": True}

@router.post("/player/{id}/ban")
def admin_ban_player(id: int, token: str, db: Session = Depends(get_db)):
    admin = require_admin(token)
    # Search for user associated with player
    conn = db.get_bind().raw_connection()
    cur = conn.cursor()
    cur.execute("UPDATE users SET role = 'banned' WHERE player_id = ?", (id,))
    conn.commit()
    cur.close()
    
    log_admin_action(0, "ban_player", "player", str(id))
    return {"success": True}

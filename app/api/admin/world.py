from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session, joinedload
from app.models import get_db, MapCell, Province, Player, TerrainType
from app.api.admin.users import require_admin, log_admin_action
from pydantic import BaseModel
from typing import List, Optional

router = APIRouter(tags=["Admin-World"])

# Request model for updating a province/map cell via admin endpoint
class AdminProvinceUpdate(BaseModel):
    terrain_id: Optional[int] = None
    is_ruin: Optional[bool] = None
    owner_id: Optional[int] = None
    reset_province: Optional[bool] = False

@router.post("/admin/world/province/{x}/{y}")
def admin_update_province(x: int, y: int, req: AdminProvinceUpdate, token: str, db: Session = Depends(get_db)):
    require_admin(token)
    
    cell = db.query(MapCell).filter(MapCell.x == x, MapCell.y == y).first()
    if not cell:
        raise HTTPException(status_code=404, detail="Cell not found")
        
    province = db.query(Province).filter(Province.world_x == x, Province.world_y == y).first()
    
    if req.terrain_id is not None:
        cell.terrain_id = req.terrain_id
        
    if req.is_ruin is not None:
        cell.is_ruin_province = req.is_ruin
        
    if req.owner_id is not None:
        cell.owner_id = req.owner_id
        if province:
            province.player_id = req.owner_id
            
    if req.reset_province and province:
        # Complex reset logic could be here (remove buildings, reset resources)
        # For now, just log it as a request
        pass
        
    db.commit()
    log_admin_action(0, "admin_update_province", "map_cell", f"{x},{y}", req.dict())
    return {"success": True}

class MapImport(BaseModel):
    map_data: List[List[str]]

class MapGenerate(BaseModel):
    width: int
    height: int
    seed: Optional[int] = None

@router.post("/admin/world/import-static")
def import_static_map(req: MapImport, token: str, db: Session = Depends(get_db)):
    require_admin(token)
    
    # Delete old map
    db.query(MapCell).delete()
    
    terrain_map = {t.name: t.id for t in db.query(TerrainType).all()}
    
    imported = 0
    for y, row in enumerate(req.map_data):
        for x, tname in enumerate(row):
            tid = terrain_map.get(tname)
            cell = MapCell(x=x, y=y, terrain_id=tid)
            db.add(cell)
            imported += 1
            
    db.commit()
    log_admin_action(0, "import_static_map", "world", None, {"cells": imported})
    return {"success": True, "imported": imported}

@router.post("/admin/world/generate")
def generate_world(req: MapGenerate, token: str, db: Session = Depends(get_db)):
    require_admin(token)
    
    db.query(MapCell).delete()
    
    # Simple generation: mostly ocean (id 1 usually) or first terrain
    first_terrain = db.query(TerrainType).first()
    tid = first_terrain.id if first_terrain else None
    
    total = 0
    for y in range(req.height):
        for x in range(req.width):
            cell = MapCell(x=x, y=y, terrain_id=tid)
            db.add(cell)
            total += 1
    
    db.commit()
    log_admin_action(0, "generate_world", "world", None, req.dict())
    return {"success": True, "total": total}

@router.get("/admin/world/map_data")
def get_admin_map_data(token: str, db: Session = Depends(get_db)):
    require_admin(token)
    cells = db.query(MapCell).options(joinedload(MapCell.terrain)).all()
    players = db.query(Player).all()
    player_colors = {p.id: getattr(p, 'color', '#cccccc') for p in players}
    
    return {
        "cells": [
            {
                "x": c.x, "y": c.y, 
                "terrain": c.terrain.name if c.terrain else "Ozean",
                "owner_id": c.owner_id,
                "bild_url": c.terrain.bild_url if c.terrain else "/terrains/ozean.gif",
                "color": player_colors.get(c.owner_id, "#ffffff") if c.owner_id else (c.terrain.color if c.terrain else "#0000ff")
            } for c in cells
        ]
    }

from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from app.models import get_db, MapCell, Province, Player, TerrainType
from app.api.admin.users import require_admin, log_admin_action
from pydantic import BaseModel
from typing import List, Optional

router = APIRouter(prefix="/admin/world", tags=["Admin-World"])

class AdminProvinceUpdate(BaseModel):
    terrain_id: Optional[int] = None
    is_ruin: Optional[bool] = None
    owner_id: Optional[int] = None
    reset_province: Optional[bool] = False

@router.post("/province/{x}/{y}")
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

@router.get("/map_data")
def get_admin_map_data(token: str, db: Session = Depends(get_db)):
    require_admin(token)
    # Similar to public map but maybe with more info
    cells = db.query(MapCell).all()
    players = db.query(Player).all()
    player_colors = {p.id: getattr(p, 'color', '#cccccc') for p in players}
    
    return {
        "cells": [
            {
                "x": c.x, "y": c.y, 
                "terrain": c.terrain.name if c.terrain else "Ozean",
                "owner_id": c.owner_id,
                "color": player_colors.get(c.owner_id, "#ffffff") if c.owner_id else (c.terrain.color if c.terrain else "#0000ff")
            } for c in cells
        ]
    }

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from app.models import get_db, MapCell, TerrainType, Player

router = APIRouter(prefix="/world", tags=["world"])


class TransferProvinceRequest(BaseModel):
    target_player_id: int


class ClaimProvinceRequest(BaseModel):
    player_id: int
    province_id: int


@router.get("/map")
def get_world_map(db: Session = Depends(get_db)):
    """Public world map overview (50x50 grid)"""
    from app.models import MapCell, Province
    cells = db.query(MapCell).order_by(MapCell.y, MapCell.x).all()
    
    # Pre-fetch all provinces to link them
    provinces = db.query(Province).all()
    prov_map = {(p.world_x, p.world_y): p.id for p in provinces}
    
    # 50x50 Grid initialisieren
    grid_terrain = [["Ozean" for _ in range(50)] for _ in range(50)]
    grid_prov_ids = [[None for _ in range(50)] for _ in range(50)]
    
    for cell in cells:
        if cell.y < 50 and cell.x < 50:
            grid_terrain[cell.y][cell.x] = cell.terrain.name if cell.terrain else "Ozean"
            grid_prov_ids[cell.y][cell.x] = prov_map.get((cell.x, cell.y))
            
    return {
        "size": 50, 
        "cells": grid_terrain,
        "province_ids": grid_prov_ids
    }

@router.get("/buildings")
def get_buildings(db: Session = Depends(get_db)):
    """Get all building types and their properties for the client"""
    from app.models import BuildingType
    buildings = db.query(BuildingType).all()
    result = []
    for b in buildings:
        # Map to expected frontend format if necessary, or just return all
        import json
        res = {
            "id": b.id,
            "name": b.name,
            "kategorie": b.kategorie,
            "baubar": bool(b.baubar),
            "arbeiter": b.arbeiter,
            "wohnraum": b.wohnraum,
            "lagerkapazitaet": b.lagerkapazitaet,
            "tech_level": b.tech_level,
            "baukosten_mips": b.baukosten_mips,
            "symbol_emoji": b.symbol_emoji,
            "produktion": json.loads(b.produktion_json) if b.produktion_json else [],
            "terrain_effektivitaet": json.loads(b.terrain_effektivitaet_json) if b.terrain_effektivitaet_json else {}
        }
        result.append(res)
    return result

@router.get("/terrains")
def get_terrains(db: Session = Depends(get_db)):
    """Get all terrain types and their properties"""
    terrains = db.query(TerrainType).all()
    result = []
    for t in terrains:
        res = {
            "id": t.id,
            "name": t.name,
            "playable": bool(t.playable),
            "color": t.color,
            "icon": t.icon,
            "description": t.beschreibung,
            "bild_url": t.bild_url,
            "gif_filename": t.gif_filename,
            "mips_kosten": t.mips_kosten,
            "holz_yield": t.holz_yield,
            "stein_yield": t.stein_yield,
            "eisen_yield": t.eisen_yield
        }
        result.append(res)
    return result

@router.get("/provinces/at")
def get_province_at(x: int, y: int, db: Session = Depends(get_db)):
    """Get detailed info about a province at specific coordinates"""
    from app.models import MapCell, Province
    cell = db.query(MapCell).filter(MapCell.x == x, MapCell.y == y).first()
    if not cell:
        raise HTTPException(status_code=404, detail="Cell not found")
    
    # Check if there is an actual province record (occupied)
    province = db.query(Province).filter(Province.world_x == x, Province.world_y == y).first()
    
    return {
        "x": x,
        "y": y,
        "terrain": cell.terrain.name if cell.terrain else "Ozean",
        "owner_id": cell.owner_id,
        "is_ruin": bool(cell.is_ruin_province),
        "province_id": province.id if province else None,
        "province_name": province.name if province else None,
        "has_bunker": province.has_bunker if province else 0
    }

@router.post("/claim")
def claim_province(request: ClaimProvinceRequest, db: Session = Depends(get_db)):
    """Open bunker to claim an empty province"""
    from app.bunker_logic import claim_province_with_bunker
    try:
        province = claim_province_with_bunker(db, request.player_id, request.province_id)
        return {
            "success": True,
            "province_id": province.id,
            "player_id": province.player_id,
            "has_bunker": True,
            "is_bunker_province": True
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/provinces/colonizable")
def get_colonizable_provinces(player_id: int, db: Session = Depends(get_db)):
    """Get all provinces that can be colonized by a player"""
    from app.siedler_logic import get_colonizable_provinces
    
    provinces = get_colonizable_provinces(db, player_id)
    
    return {
        "player_id": player_id,
        "colonizable_provinces": provinces
    }


@router.post("/provinces/{province_id}/transfer")
def request_province_transfer(province_id: int, request: TransferProvinceRequest, db: Session = Depends(get_db)):
    """Request transfer of province to another player"""
    from app.models import Province, Player
    from app.siedler_logic import transfer_province
    
    province = db.query(Province).filter(Province.id == province_id).first()
    if not province:
        raise HTTPException(status_code=404, detail="Province not found")
    
    player = db.query(Player).filter(Player.id == request.target_player_id).first()
    if not player:
        raise HTTPException(status_code=404, detail="Target player not found")
    
    try:
        result = transfer_province(db, province_id, province.player_id, request.target_player_id)
        return {
            "success": True,
            "province_id": province_id,
            "new_owner_id": request.target_player_id,
            "message": f"Province transferred to player {request.target_player_id}"
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/provinces/{province_id}/transfer/history")
def get_transfer_history(province_id: int, db: Session = Depends(get_db)):
    """Get transfer history for a province"""
    from app.models import GameLog
    
    logs = db.query(GameLog).filter(
        GameLog.province_id == province_id,
        GameLog.event_type.in_(["PROVINCE_TRANSFERRED", "PROVINCE_COLONIZED"])
    ).order_by(GameLog.timestamp.desc()).limit(20).all()
    
    result = []
    for log in logs:
        import json
        result.append({
            "id": log.id,
            "timestamp": log.timestamp.isoformat() if log.timestamp else None,
            "event_type": log.event_type,
            "message": log.message,
            "details": json.loads(log.details_json) if log.details_json else {}
        })
    
    return {
        "province_id": province_id,
        "history": result
    }
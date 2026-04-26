from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session, joinedload
from app.models import get_db, MapCell, Province, Player, TerrainType
from app.api.admin.users import require_admin, log_admin_action
from pydantic import BaseModel
from typing import List, Optional, Dict
import random

router = APIRouter(tags=["Admin-World"])

# Request model for updating a province/map cell via admin endpoint
class AdminProvinceUpdate(BaseModel):
    terrain_id: Optional[int] = None
    is_ruin: Optional[bool] = None
    owner_id: Optional[int] = None
    reset_province: Optional[bool] = False

class CellUpdate(BaseModel):
    x: int
    y: int
    terrain_id: int

class BulkCellUpdate(BaseModel):
    cells: List[CellUpdate]

@router.post("/world/province/{x}/{y}")
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

@router.post("/world/map/cells/bulk")
def admin_bulk_update_cells(req: BulkCellUpdate, token: str, db: Session = Depends(get_db)):
    require_admin(token)
    
    updated = 0
    for cell_req in req.cells:
        cell = db.query(MapCell).filter(MapCell.x == cell_req.x, MapCell.y == cell_req.y).first()
        if cell:
            cell.terrain_id = cell_req.terrain_id
            updated += 1
        else:
            # Create if missing? usually admin only edits existing, but let's be robust
            new_cell = MapCell(x=cell_req.x, y=cell_req.y, terrain_id=cell_req.terrain_id)
            db.add(new_cell)
            updated += 1
            
    db.commit()
    log_admin_action(0, "admin_bulk_update_cells", "world", None, {"count": updated})
    return {"success": True, "updated": updated}

class MapImport(BaseModel):
    map_data: List[List[str]]

class MapGenerate(BaseModel):
    width: int
    height: int
    seed: Optional[int] = None
    excluded_terrain_ids: Optional[List[int]] = []

@router.post("/world/import-static")
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

@router.post("/world/generate")
def generate_world(req: MapGenerate, token: str, db: Session = Depends(get_db)):
    require_admin(token)
    
    db.query(MapCell).delete()
    
    if req.seed is not None:
        random.seed(req.seed)
    
    # Terrain IDs from DB
    all_terrains = db.query(TerrainType).all()
    terrains = {t.name: t.id for t in all_terrains}
    excluded = set(req.excluded_terrain_ids or [])
    
    def get_tid(name, fallback_id):
        tid = terrains.get(name)
        if tid in excluded: return None
        return tid

    # Groups
    ocean_id = terrains.get("Ozean", 33)
    
    mountain_ids = [get_tid("Felsgebirge", 14), get_tid("Ödgebirge", 16), get_tid("Brachgebirge", 32), get_tid("Sanddünen", 13)]
    mountain_ids = [t for t in mountain_ids if t is not None]
    
    hill_ids = [get_tid("Ödhügel", 15), get_tid("Brachhügel", 31), get_tid("Grangerhügel", 7), get_tid("Stepphügel", 17)]
    hill_ids = [t for t in hill_ids if t is not None]
    
    # Backdrop dry terrains
    dry_ids = [get_tid("Wüste", 10), get_tid("Sanddünen", 13), get_tid("Ödfelsland", 19)]
    dry_ids = [t for t in dry_ids if t is not None]
    
    # Backdrop wastelands
    waste_ids = [get_tid("Ödland", 3), get_tid("Brachland", 29), get_tid("Steppe", 2)]
    waste_ids = [t for t in waste_ids if t is not None]
    
    # Oasis
    oasis_ids = [get_tid("Wald", 4), get_tid("Grasland", 1), get_tid("Grünland", 21)]
    oasis_ids = [t for t in oasis_ids if t is not None]

    fallback_base = dry_ids[0] if dry_ids else (waste_ids[0] if waste_ids else ocean_id)

    # Hierarchical Seeds
    seeds = [] # (x, y, terrain_id, influence_radius, priority)
    
    # 0. Ocean Seeds (Coasts & Lakes)
    # Coastal seeds along borders to create protrusions
    for _ in range(15):
        side = random.randint(0, 3)
        if side == 0: sx, sy = 0, random.randint(0, req.height-1)
        elif side == 1: sx, sy = req.width-1, random.randint(0, req.height-1)
        elif side == 2: sx, sy = random.randint(0, req.width-1), 0
        else: sx, sy = random.randint(0, req.width-1), req.height-1
        seeds.append((sx, sy, ocean_id, random.uniform(4, 7), 50)) # High priority coast
        
    # Inland lakes
    num_lakes = random.randint(3, 5)
    for _ in range(num_lakes):
        seeds.append((random.randint(5, req.width-6), random.randint(5, req.height-6), 
                      ocean_id, random.uniform(2, 4), 15))

    # 1. Mountain Ranges (Spines)
    num_spines = random.randint(3, 6)
    for _ in range(num_spines):
        lx, ly = random.randint(5, req.width-6), random.randint(5, req.height-6)
        spine_len = random.randint(4, 10)
        dx, dy = random.uniform(-1.5, 1.5), random.uniform(-1.5, 1.5)
        m_tid = random.choice(mountain_ids) if mountain_ids else fallback_base
        for i in range(spine_len):
            px, py = int(lx + i*dx), int(ly + i*dy)
            if 1 <= px < req.width-1 and 1 <= py < req.height-1:
                # Smaller mountain cluster
                m_rad = random.randint(2, 4)
                seeds.append((px, py, m_tid, m_rad, 10)) # Mountains
                # Add Hill border around each spine point
                if hill_ids:
                    # Hill border with slightly larger radius than mountains to surround them
                    seeds.append((px+random.randint(-1,1), py+random.randint(-1,1), random.choice(hill_ids), m_rad + 1.5, 5))
                    
    # 2. General Dry Clusters (Wüste/Sand) - More but smaller
    num_dry = (req.width * req.height) // 100
    for _ in range(num_dry):
        seeds.append((random.randint(2, req.width-3), random.randint(2, req.height-3), 
                      random.choice(dry_ids) if dry_ids else fallback_base, random.uniform(3, 5), 2))

    # 3. Wasteland Background - More but smaller
    num_waste = (req.width * req.height) // 200
    for _ in range(num_waste):
        seeds.append((random.randint(2, req.width-3), random.randint(2, req.height-3), 
                      random.choice(waste_ids) if waste_ids else fallback_base, random.uniform(4, 6), 1))

    # 4. Small Oases (4-9 fields)
    num_oases = random.randint(3, 6)
    oases_points = []
    for _ in range(num_oases):
        ox, oy = random.randint(5, req.width-6), random.randint(5, req.height-6)
        o_tid = random.choice(oasis_ids) if oasis_ids else fallback_base
        size = random.randint(4, 9)
        # Place a tight cluster of points
        for _ in range(size):
            seeds.append((ox + random.randint(-1, 1), oy + random.randint(-1, 1), o_tid, 1.5, 20))

    total = 0
    for y in range(req.height):
        for x in range(req.width):
            # 1. Borders are ALWAYS ocean
            if x == 0 or x == req.width - 1 or y == 0 or y == req.height - 1:
                tid = ocean_id
            else:
                # 2. Nearest prioritized seed
                best_score = -1
                tid = fallback_base
                
                for sx, sy, stid, srad, sprio in seeds:
                    dist = ((x - sx)**2 + (y - sy)**2)**0.5
                    if dist <= srad:
                        # Priority based choice: Distance + Priority
                        score = sprio * (1.0 - (dist / srad))
                        if score > best_score:
                            best_score = score
                            tid = stid
                            
                # Fallback to background noise if no seed reached here
                if best_score < 0:
                    # Prefer dry backgrounds
                    if random.random() < 0.7:
                        tid = random.choice(dry_ids) if dry_ids else fallback_base
                    else:
                        tid = random.choice(waste_ids) if waste_ids else fallback_base

            cell = MapCell(x=x, y=y, terrain_id=tid)
            db.add(cell)
            total += 1
    
    db.commit()
    log_admin_action(0, "generate_world", "world", None, req.dict())
    return {"success": True, "total": total}

@router.get("/world/map_data")
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

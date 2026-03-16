from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from app.models import get_db, BuildingTemplate, Resource, Regierungsform, TerrainType, Article, Vorkommen, AnimalTemplate, UnitType, ProvinceField
from app.api.admin.users import require_admin, log_admin_action
from pydantic import BaseModel
from typing import Dict, Any, Optional, List

router = APIRouter(prefix="/admin", tags=["Admin-Data-Editors"])

# Generic PATCH endpoint for entities
@router.patch("/{entity}/{id}")
def patch_entity(entity: str, id: int, data: Dict[str, Any], token: str, db: Session = Depends(get_db)):
    require_admin(token)
    
    model_map = {
        "gebaeude_typen": BuildingTemplate,
        "rohstoffe": Resource,
        "regierungsformen": Regierungsform,
        "terrain": TerrainType,
        "artikel": Article,
        "vorkommen": Vorkommen,
        "lebewesen": AnimalTemplate,
        "einheiten": UnitType,
        "gebaeude_felder": ProvinceField
    }
    
    if entity not in model_map:
        raise HTTPException(status_code=400, detail=f"Entity {entity} not supported for PATCH")
        
    model = model_map[entity]
    item = db.query(model).filter(model.id == id).first()
    
    if not item:
        raise HTTPException(status_code=404, detail=f"{entity} with id {id} not found")
        
    for key, value in data.items():
        if hasattr(item, key):
            # Special handling for JSON fields if needed, but usually we just set it
            setattr(item, key, value)
            
    db.commit()
    log_admin_action(0, f"patch_{entity}", entity, str(id), data)
    return {"success": True}

# Specific GET endpoints for data editors to provide enriched data

@router.get("/gebaeude_typen")
def get_admin_buildings(token: str, db: Session = Depends(get_db)):
    require_admin(token)
    buildings = db.query(BuildingTemplate).all()
    # Enriched data like top 3 products or special tags can be calculated here or in frontend
    return buildings

@router.get("/rohstoffe")
def get_admin_resources(token: str, db: Session = Depends(get_db)):
    require_admin(token)
    return db.query(Resource).all()

@router.get("/regierungsformen")
def get_admin_govs(token: str, db: Session = Depends(get_db)):
    require_admin(token)
    return db.query(Regierungsform).all()

@router.get("/terrain")
def get_admin_terrain(token: str, db: Session = Depends(get_db)):
    require_admin(token)
    return db.query(TerrainType).all()

@router.get("/artikel")
def get_admin_artikel(token: str, db: Session = Depends(get_db)):
    require_admin(token)
    return db.query(Article).all()

@router.get("/vorkommen")
def get_admin_vorkommen(token: str, db: Session = Depends(get_db)):
    require_admin(token)
    return db.query(Vorkommen).all()

@router.get("/lebewesen")
def get_admin_lebewesen(token: str, db: Session = Depends(get_db)):
    require_admin(token)
    return db.query(AnimalTemplate).all()

@router.get("/einheiten")
def get_admin_einheiten(token: str, db: Session = Depends(get_db)):
    require_admin(token)
    return db.query(UnitType).all()

@router.get("/gebaeude_felder")
def get_admin_gebaeude_felder(token: str, db: Session = Depends(get_db)):
    require_admin(token)
    return db.query(ProvinceField).all()

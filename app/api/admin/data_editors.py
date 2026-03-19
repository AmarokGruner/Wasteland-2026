from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from app.models import get_db, BuildingTemplate, Resource, Regierungsform, TerrainType, Article, Vorkommen, AnimalTemplate, UnitType, ProvinceField
from app.api.admin.users import require_admin, log_admin_action
from pydantic import BaseModel
from typing import Dict, Any, Optional, List

router = APIRouter(tags=["Admin-Data-Editors"])

MODEL_MAP = {
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

# Specific ID-based GET endpoints for priority entities
@router.get("/gebaeude_typen/{id}")
def get_building_type_by_id(id: int, token: str, db: Session = Depends(get_db)):
    require_admin(token)
    item = db.query(BuildingTemplate).filter(BuildingTemplate.id == id).first()
    if not item:
        raise HTTPException(status_code=404, detail="Gebäude-Typ nicht gefunden")
    return item

@router.get("/rohstoffe/{id}")
def get_resource_by_id(id: int, token: str, db: Session = Depends(get_db)):
    require_admin(token)
    item = db.query(Resource).filter(Resource.id == id).first()
    if not item:
        raise HTTPException(status_code=404, detail="Ressource nicht gefunden")
    return item

# Generic CRUD endpoints for entities (must be at the bottom)
@router.get("/{entity}/{id}")
def generic_get_entity(entity: str, id: int, token: str, db: Session = Depends(get_db)):
    require_admin(token)
    if entity not in MODEL_MAP:
        raise HTTPException(status_code=400, detail=f"Entity {entity} not supported")
    model = MODEL_MAP[entity]
    item = db.query(model).filter(model.id == id).first()
    if not item:
        raise HTTPException(status_code=404, detail=f"{entity} with id {id} not found")
    return item

@router.patch("/{entity}/{id}")
def generic_patch_entity(entity: str, id: int, data: Dict[str, Any], token: str, db: Session = Depends(get_db)):
    require_admin(token)
    if entity not in MODEL_MAP:
        raise HTTPException(status_code=400, detail=f"Entity {entity} not supported for PATCH")
    model = MODEL_MAP[entity]
    item = db.query(model).filter(model.id == id).first()
    if not item:
        raise HTTPException(status_code=404, detail=f"{entity} with id {id} not found")
        
    for key, value in data.items():
        if hasattr(item, key):
            import json
            if isinstance(value, (dict, list)):
                setattr(item, key, json.dumps(value))
            else:
                setattr(item, key, value)
            
    db.commit()
    log_admin_action(0, f"patch_{entity}", entity, str(id), data)
    return {"success": True}

@router.post("/{entity}")
def generic_create_entity(entity: str, data: Dict[str, Any], token: str, db: Session = Depends(get_db)):
    require_admin(token)
    if entity not in MODEL_MAP:
        raise HTTPException(status_code=400, detail=f"Entity {entity} not supported for POST")
    model = MODEL_MAP[entity]
    import json
    item = model()
    for key, value in data.items():
        if hasattr(item, key):
            if isinstance(value, (dict, list)):
                setattr(item, key, json.dumps(value))
            else:
                setattr(item, key, value)
    db.add(item)
    db.commit()
    db.refresh(item)
    log_admin_action(0, f"create_{entity}", entity, str(item.id), data)
    return {"success": True, "id": item.id}

@router.delete("/{entity}/{id}")
def generic_delete_entity(entity: str, id: int, token: str, db: Session = Depends(get_db)):
    require_admin(token)
    if entity not in MODEL_MAP:
        raise HTTPException(status_code=400, detail=f"Entity {entity} not supported for DELETE")
    model = MODEL_MAP[entity]
    item = db.query(model).filter(model.id == id).first()
    if not item:
        raise HTTPException(status_code=404, detail=f"{entity} with id {id} not found")
    db.delete(item)
    db.commit()
    log_admin_action(0, f"delete_{entity}", entity, str(id), None)
    return {"success": True}

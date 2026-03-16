from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from app.models import get_db, CityExpansionConfig, Province, ProvinceField, BuildingInstance
from app.api.admin.users import require_admin
from pydantic import BaseModel
from typing import List, Dict, Any

router = APIRouter(tags=["Admin-City-Grid"])

class CityConfigSave(BaseModel):
    level: int
    unlocked_fields: List[int]

@router.get("/city-config")
def get_city_config(token: str, db: Session = Depends(get_db)):
    require_admin(token)
    configs = db.query(CityExpansionConfig).all()
    return {c.level: c.unlocked_fields for c in configs}

@router.post("/city-config")
def save_city_config(data: CityConfigSave, token: str, db: Session = Depends(get_db)):
    require_admin(token)
    config = db.query(CityExpansionConfig).filter(CityExpansionConfig.level == data.level).first()
    if not config:
        config = CityExpansionConfig(level=data.level)
        db.add(config)
    
    config.unlocked_fields = data.unlocked_fields
    db.commit()
    
    # Optional: Update existing provinces? 
    # Usually, this should only affect new expansions or requires a separate sync task.
    
    return {"success": True}

@router.post("/city-config/sync-provinces")
def sync_provinces(token: str, db: Session = Depends(get_db)):
    """Initializes province_fields for all provinces if not already present."""
    require_admin(token)
    provinces = db.query(Province).all()
    count = 0
    for p in provinces:
        # Check if fields already exist
        exists = db.query(ProvinceField).filter(ProvinceField.province_id == p.id).first()
        if not exists:
            # Create 15x15 grid
            for i in range(225):
                field = ProvinceField(
                    id=i,
                    province_id=p.id,
                    x=i % 15,
                    y=i // 15,
                    type="land",
                    city_unlock_level=0
                )
                db.add(field)
            count += 1
    
    db.commit()
    return {"success": True, "provinces_initialized": count}

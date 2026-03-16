from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from app.models import get_db, Province, ProvinceField, BuildingInstance, BuildingType, CityExpansionConfig
from app.building_logic import build_building, can_build, deduct_resources, get_lager_dict, demolish_building
from pydantic import BaseModel
from typing import List, Optional
import json

router = APIRouter(prefix="/province", tags=["City-Grid"])

class BuildRequest(BaseModel):
    template_id: int
    field_id: int

@router.get("/{province_id}/fields")
def get_province_fields(province_id: int, db: Session = Depends(get_db)):
    province = db.query(Province).filter(Province.id == province_id).first()
    if not province:
        raise HTTPException(status_code=404, detail="Provinz nicht gefunden")
    
    fields = db.query(ProvinceField).filter(ProvinceField.province_id == province_id).order_by(ProvinceField.id).all()
    
    # If no fields yet, initialize them (lazy initialization)
    if not fields:
        for i in range(225):
            field = ProvinceField(
                id=i,
                province_id=province_id,
                x=i % 15,
                y=i // 15,
                type="land",
                city_unlock_level=0
            )
            db.add(field)
        db.commit()
        fields = db.query(ProvinceField).filter(ProvinceField.province_id == province_id).order_by(ProvinceField.id).all()

    result = []
    for f in fields:
        building_name = None
        if f.occupied_building_id:
            instance = db.query(BuildingInstance).filter(BuildingInstance.id == f.occupied_building_id).first()
            if instance:
                building_name = instance.type.name
        
        result.append({
            "id": f.id,
            "x": f.x,
            "y": f.y,
            "type": f.type,
            "unlock_level": f.city_unlock_level,
            "occupied": building_name,
            "texture": "concrete" if f.type == "city" else "grass"
        })
    
    return result

@router.post("/{province_id}/build")
def player_build(province_id: int, req: BuildRequest, db: Session = Depends(get_db)):
    # Perform build via centralized logic
    # The logic inside build_building (and can_build) now handles:
    # - Field existence & occupancy
    # - Unlock levels
    # - Bautyp constraints
    # - Resource/MIPS deduction
    # - Stadtausbau leveling
    
    field = db.query(ProvinceField).filter(ProvinceField.province_id == province_id, ProvinceField.id == req.field_id).first()
    if not field:
        raise HTTPException(status_code=404, detail="Feld nicht gefunden")

    instance_data = build_building(db, req.template_id, province_id, field.x, field.y)
    
    return {"success": True, "instance": instance_data}

@router.post("/{province_id}/demolish/{field_id}")
def player_demolish(province_id: int, field_id: int, db: Session = Depends(get_db)):
    field = db.query(ProvinceField).filter(ProvinceField.province_id == province_id, ProvinceField.id == field_id).first()
    if not field or not field.occupied_building_id:
        raise HTTPException(status_code=404, detail="Kein Gebäude auf diesem Feld gefunden")
    
    result = demolish_building(db, field.occupied_building_id)
    return result

@router.get("/{province_id}/city-status")
def get_city_status(province_id: int, db: Session = Depends(get_db)):
    province = db.query(Province).filter(Province.id == province_id).first()
    if not province:
        raise HTTPException(status_code=404, detail="Provinz nicht gefunden")
    
    next_building = "Metropole" # Placeholder
    if province.next_required_building_id:
        nb = db.query(BuildingType).filter(BuildingType.id == province.next_required_building_id).first()
        if nb:
            next_building = nb.name
            
    return {
        "current_level": province.current_city_level,
        "next_building": next_building,
        "size_level_name": ["Camp", "Siedlung", "Dorf", "Kleinstadt", "Stadt", "Großstadt", "Metropole", "Megapolis", "Hauptstadt"][province.current_city_level] if province.current_city_level <= 8 else "Unbekannt"
    }

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from app.models import get_db, Province, Player, Vorkommen, ProvinceDeposit, TerrainConfig, ProvinceAnimal, AnimalTemplate, ProvinceLager, Resource
from app.animal_logic import process_wild_animal_feeding, process_breeding

router = APIRouter(prefix="/province", tags=["province"])

class IrrigateRequest(BaseModel):
    water_amount: float

class SearchDepositRequest(BaseModel):
    vorkommen_id: int

class ReleaseAnimalsRequest(BaseModel):
    animal_resource_id: int
    count: int

class AssignAnimalsRequest(BaseModel):
    building_instance_id: int
    animal_resource_id: int

@router.get("/{province_id}/climate")
def get_province_climate(province_id: int, db: Session = Depends(get_db)):
    from app.climate_logic import get_climate_data
    climate = get_climate_data(db, province_id)
    if not climate:
        raise HTTPException(status_code=404, detail="Province not found")
    return climate

@router.post("/{province_id}/irrigate")
def irrigate_province(province_id: int, request: IrrigateRequest, db: Session = Depends(get_db)):
    from app.climate_logic import irrigate_province
    result = irrigate_province(db, province_id, request.water_amount)
    return result

@router.get("/{province_id}/deposits")
def get_province_deposits(province_id: int, db: Session = Depends(get_db)):
    province = db.query(Province).filter(Province.id == province_id).first()
    if not province:
        raise HTTPException(status_code=404, detail="Province not found")
    
    player = db.query(Player).filter(Player.id == province.player_id).first()
    all_vorkommen = db.query(Vorkommen).all()
    
    result_deposits = []
    for v in all_vorkommen:
        prob = v.get_probability(province.terrain)
        
        prov_deposit = db.query(ProvinceDeposit).filter(
            ProvinceDeposit.province_id == province_id,
            ProvinceDeposit.vorkommen_id == v.id
        ).first()
        
        can_search = (
            player.tech_level >= v.tech and 
            prob is not None and 
            prob > 0 and
            (not prov_deposit or not prov_deposit.deposit_searched)
        )
        
        result_deposits.append({
            "vorkommen_id": v.id,
            "name": v.name,
            "typ": v.typ,
            "tech_level": v.tech,
            "suchkosten_mips": v.suchkosten,
            "probability": prob,
            "searched": bool(prov_deposit.deposit_searched) if prov_deposit else False,
            "found": bool(prov_deposit.deposit_found) if prov_deposit else False,
            "quality": prov_deposit.quality if prov_deposit and prov_deposit.deposit_found else None,
            "can_search": can_search
        })
    
    return {
        "province_id": province_id,
        "terrain": province.terrain,
        "deposits": result_deposits
    }

@router.get("/{province_id}/deposits/searchable")
def get_searchable_deposits(province_id: int, db: Session = Depends(get_db)):
    province = db.query(Province).filter(Province.id == province_id).first()
    if not province:
        raise HTTPException(status_code=404, detail="Province not found")
    
    player = db.query(Player).filter(Player.id == province.player_id).first()
    all_vorkommen = db.query(Vorkommen).all()
    
    result_deposits = []
    for v in all_vorkommen:
        prob = v.get_probability(province.terrain)
        
        if not prob or prob <= 0:
            continue
        
        if player.tech_level < v.tech:
            continue
        
        prov_deposit = db.query(ProvinceDeposit).filter(
            ProvinceDeposit.province_id == province_id,
            ProvinceDeposit.vorkommen_id == v.id
        ).first()
        
        if prov_deposit and prov_deposit.deposit_searched:
            continue
        
        result_deposits.append({
            "vorkommen_id": v.id,
            "name": v.name,
            "typ": v.typ,
            "tech_level": v.tech,
            "suchkosten_mips": v.suchkosten,
            "probability": prob
        })
    
    return {
        "province_id": province_id,
        "terrain": province.terrain,
        "searchable_deposits": result_deposits
    }

@router.post("/{province_id}/deposits/search")
def search_deposit(province_id: int, request: SearchDepositRequest, db: Session = Depends(get_db)):
    import random
    from app.round_logic import QUALITY_MULTIPLIERS
    
    province = db.query(Province).filter(Province.id == province_id).first()
    if not province:
        raise HTTPException(status_code=404, detail="Province not found")
    
    vorkommen = db.query(Vorkommen).filter(
        Vorkommen.id == request.vorkommen_id
    ).first()
    
    if not vorkommen:
        raise HTTPException(status_code=404, detail="Vorkommen not found")
    
    player = db.query(Player).filter(Player.id == province.player_id).first()
    
    if player.tech_level < vorkommen.tech:
        raise HTTPException(status_code=400, detail=f"TECH_TOO_LOW: {player.tech_level}/{vorkommen.tech}")
    
    prob = vorkommen.get_probability(province.terrain)
    if not prob or prob <= 0:
        raise HTTPException(status_code=400, detail="NOT_POSSIBLE_IN_TERRAIN")
    
    prov_deposit = db.query(ProvinceDeposit).filter(
        ProvinceDeposit.province_id == province_id,
        ProvinceDeposit.vorkommen_id == vorkommen.id
    ).first()
    
    if prov_deposit and prov_deposit.deposit_searched:
        raise HTTPException(status_code=400, detail="ALREADY_SEARCHED")
    
    if province.mips < vorkommen.suchkosten:
        raise HTTPException(status_code=400, detail=f"INSUFFICIENT_MIPS: {province.mips}/{vorkommen.suchkosten}")
    
    province.mips -= vorkommen.suchkosten
    
    roll = random.randint(1, 100)
    found = roll <= prob
    
    if found:
        quality = random.choices([1, 2, 3], weights=[0.4, 0.4, 0.2])[0]
    else:
        quality = None
    
    if not prov_deposit:
        prov_deposit = ProvinceDeposit(
            province_id=province_id,
            vorkommen_id=vorkommen.id,
            deposit_found=int(found),
            deposit_searched=1,
            quality=quality if found else 2
        )
        db.add(prov_deposit)
    else:
        prov_deposit.deposit_searched = 1
        prov_deposit.deposit_found = int(found)
        if found:
            prov_deposit.quality = quality
    
    db.commit()
    
    return {
        "success": True,
        "found": found,
        "quality": quality,
        "cost": vorkommen.suchkosten,
        "mips_remaining": province.mips
    }

# New endpoints for animal management
@router.get("/{province_id}/animals")
def get_province_animals(province_id: int, db: Session = Depends(get_db)):
    province = db.query(Province).filter(Province.id == province_id).first()
    if not province:
        raise HTTPException(status_code=404, detail="Province not found")
    
    wild_animals = db.query(ProvinceAnimal).filter(
        ProvinceAnimal.province_id == province_id,
        ProvinceAnimal.is_wild == 1
    ).all()
    
    breeding_animals = db.query(ProvinceAnimal).filter(
        ProvinceAnimal.province_id == province_id,
        ProvinceAnimal.is_wild == 0
    ).all()
    
    def serialize(animal):
        res = db.query(Resource).filter(Resource.id == animal.animal_resource_id).first()
        return {
            "animal_resource_id": animal.animal_resource_id,
            "name": res.name if res else "",
            "count": animal.count,
            "is_wild": bool(animal.is_wild),
            "building_instance_id": animal.building_instance_id
        }
    
    return {
        "province_id": province_id,
        "wild": [serialize(a) for a in wild_animals],
        "breeding": [serialize(a) for a in breeding_animals],
        "terrain_yield_malus": province.terrain_yield_malus
    }

@router.post("/{province_id}/animals/release")
def release_animals(province_id: int, request: ReleaseAnimalsRequest, db: Session = Depends(get_db)):
    province = db.query(Province).filter(Province.id == province_id).first()
    if not province:
        raise HTTPException(status_code=404, detail="Province not found")
    
    animal = db.query(ProvinceAnimal).filter(
        ProvinceAnimal.province_id == province_id,
        ProvinceAnimal.animal_resource_id == request.animal_resource_id,
        ProvinceAnimal.is_wild == 0
    ).first()
    if not animal or animal.count < request.count:
        raise HTTPException(status_code=400, detail="Not enough animals to release")
    
    # Reduce breeding stock
    animal.count -= request.count
    if animal.count == 0:
        db.delete(animal)
    
    # Add to wild stock (or just increase wild count in lager)
    wild = db.query(ProvinceAnimal).filter(
        ProvinceAnimal.province_id == province_id,
        ProvinceAnimal.animal_resource_id == request.animal_resource_id,
        ProvinceAnimal.is_wild == 1
    ).first()
    if not wild:
        wild = ProvinceAnimal(
            province_id=province_id,
            animal_resource_id=request.animal_resource_id,
            count=request.count,
            is_wild=1
        )
        db.add(wild)
    else:
        wild.count += request.count
    
    db.commit()
    return {"success": True, "released": request.count}

@router.post("/{province_id}/animals/assign")
def assign_animals(province_id: int, request: AssignAnimalsRequest, db: Session = Depends(get_db)):
    # Assign wild animals to a breeding building
    province = db.query(Province).filter(Province.id == province_id).first()
    if not province:
        raise HTTPException(status_code=404, detail="Province not found")
    
    # Verify building exists and belongs to province
    from app.models import BuildingInstance
    building = db.query(BuildingInstance).filter(
        BuildingInstance.id == request.building_instance_id,
        BuildingInstance.provinz_id == province_id
    ).first()
    if not building:
        raise HTTPException(status_code=404, detail="Building instance not found")
    
    # Verify building is a Tierzucht building (check special_eigenschaften for 'tierzucht')
    import json
    spec = json.loads(building.type.spezial_eigenschaften or "{}")
    if "tierzucht" not in spec:
        raise HTTPException(status_code=400, detail="Building is not a Tierzucht building")
    
    # Verify enough wild animals exist
    wild = db.query(ProvinceAnimal).filter(
        ProvinceAnimal.province_id == province_id,
        ProvinceAnimal.animal_resource_id == request.animal_resource_id,
        ProvinceAnimal.is_wild == 1
    ).first()
    if not wild or wild.count < 1:
        raise HTTPException(status_code=400, detail="No wild animals of this type available")
    
    # Move one animal to breeding (for simplicity, assign all count)
    # Decrease wild count
    move_count = wild.count
    wild.count = 0
    db.delete(wild)
    
    # Create breeding record
    breeding = db.query(ProvinceAnimal).filter(
        ProvinceAnimal.province_id == province_id,
        ProvinceAnimal.animal_resource_id == request.animal_resource_id,
        ProvinceAnimal.is_wild == 0
    ).first()
    if not breeding:
        breeding = ProvinceAnimal(
            province_id=province_id,
            animal_resource_id=request.animal_resource_id,
            count=move_count,
            is_wild=0,
            building_instance_id=request.building_instance_id
        )
        db.add(breeding)
    else:
        breeding.count += move_count
        breeding.building_instance_id = request.building_instance_id
    
    db.commit()
    return {"success": True, "assigned": move_count}

@router.get("/{province_id}/animals/preview")
def preview_animal_actions(province_id: int, db: Session = Depends(get_db)):
    # Show feeding costs and expected breeding output for next tick
    province = db.query(Province).filter(Province.id == province_id).first()
    if not province:
        raise HTTPException(status_code=404, detail="Province not found")
    
    # Gather wild animal feeding needs
    wild_animals = db.query(ProvinceAnimal).filter(
        ProvinceAnimal.province_id == province_id,
        ProvinceAnimal.is_wild == 1
    ).all()
    
    feeding_needs = []
    for animal in wild_animals:
        template = db.query(AnimalTemplate).filter(AnimalTemplate.resource_id == animal.animal_resource_id).first()
        if not template or not template.is_pflanzenfresser:
            continue
        feed_needed = animal.count * template.feed_amount_per_24h
        feed_res = db.query(Resource).filter(Resource.id == template.feed_resource_id).first()
        feeding_needs.append({
            "animal_resource_id": animal.animal_resource_id,
            "animal_name": db.query(Resource).filter(Resource.id == animal.animal_resource_id).first().name,
            "feed_resource_id": template.feed_resource_id,
            "feed_resource_name": feed_res.name if feed_res else "",
            "feed_needed": feed_needed
        })
    
    # Breeding preview (for each breeding building)
    breeding_preview = []
    breeding_animals = db.query(ProvinceAnimal).filter(
        ProvinceAnimal.province_id == province_id,
        ProvinceAnimal.is_wild == 0
    ).all()
    for animal in breeding_animals:
        template = db.query(AnimalTemplate).filter(AnimalTemplate.resource_id == animal.animal_resource_id).first()
        if not template:
            continue
        # Expected new animals per day
        expected_new = int(animal.count * template.breed_rate)
        output_res = db.query(Resource).filter(Resource.id == template.breed_output_resource_id).first() if template.breed_output_resource_id else None
        breeding_preview.append({
            "animal_resource_id": animal.animal_resource_id,
            "animal_name": db.query(Resource).filter(Resource.id == animal.animal_resource_id).first().name,
            "expected_new": expected_new,
            "output_resource_id": template.breed_output_resource_id,
            "output_resource_name": output_res.name if output_res else None
        })
    
    return {
        "province_id": province_id,
        "feeding_needs": feeding_needs,
        "breeding_preview": breeding_preview,
        "terrain_yield_malus": province.terrain_yield_malus
    }

# Existing endpoints for settings, etc. (unchanged)


@router.get("/{province_id}/deposits/searchable")
def get_searchable_deposits(province_id: int, db: Session = Depends(get_db)):
    province = db.query(Province).filter(Province.id == province_id).first()
    if not province:
        raise HTTPException(status_code=404, detail="Province not found")
    
    player = db.query(Player).filter(Player.id == province.player_id).first()
    all_vorkommen = db.query(Vorkommen).all()
    
    result_deposits = []
    for v in all_vorkommen:
        prob = v.get_probability(province.terrain)
        
        if not prob or prob <= 0:
            continue
        
        if player.tech_level < v.tech:
            continue
        
        prov_deposit = db.query(ProvinceDeposit).filter(
            ProvinceDeposit.province_id == province_id,
            ProvinceDeposit.vorkommen_id == v.id
        ).first()
        
        if prov_deposit and prov_deposit.deposit_searched:
            continue
        
        result_deposits.append({
            "vorkommen_id": v.id,
            "name": v.name,
            "typ": v.typ,
            "tech_level": v.tech,
            "suchkosten_mips": v.suchkosten,
            "probability": prob
        })
    
    return {
        "province_id": province_id,
        "terrain": province.terrain,
        "searchable_deposits": result_deposits
    }

@router.post("/{province_id}/deposits/search")
def search_deposit(province_id: int, request: SearchDepositRequest, db: Session = Depends(get_db)):
    import random
    from app.round_logic import QUALITY_MULTIPLIERS
    
    province = db.query(Province).filter(Province.id == province_id).first()
    if not province:
        raise HTTPException(status_code=404, detail="Province not found")
    
    vorkommen = db.query(Vorkommen).filter(
        Vorkommen.id == request.vorkommen_id
    ).first()
    
    if not vorkommen:
        raise HTTPException(status_code=404, detail="Vorkommen not found")
    
    player = db.query(Player).filter(Player.id == province.player_id).first()
    
    if player.tech_level < vorkommen.tech:
        raise HTTPException(status_code=400, detail=f"TECH_TOO_LOW: {player.tech_level}/{vorkommen.tech}")
    
    prob = vorkommen.get_probability(province.terrain)
    if not prob or prob <= 0:
        raise HTTPException(status_code=400, detail="NOT_POSSIBLE_IN_TERRAIN")
    
    prov_deposit = db.query(ProvinceDeposit).filter(
        ProvinceDeposit.province_id == province_id,
        ProvinceDeposit.vorkommen_id == vorkommen.id
    ).first()
    
    if prov_deposit and prov_deposit.deposit_searched:
        raise HTTPException(status_code=400, detail="ALREADY_SEARCHED")
    
    if province.mips < vorkommen.suchkosten_mips:
        raise HTTPException(status_code=400, detail=f"INSUFFICIENT_MIPS: {province.mips}/{vorkommen.suchkosten_mips}")
    
    province.mips -= vorkommen.suchkosten_mips
    
    roll = random.randint(1, 100)
    found = roll <= prob
    
    if found:
        quality = random.choices([1, 2, 3], weights=[0.4, 0.4, 0.2])[0]
    else:
        quality = None
    
    if not prov_deposit:
        prov_deposit = ProvinceDeposit(
            province_id=province_id,
            vorkommen_id=vorkommen.id,
            deposit_found=int(found),
            deposit_searched=1,
            quality=quality if found else 2
        )
        db.add(prov_deposit)
    else:
        prov_deposit.deposit_searched = 1
        prov_deposit.deposit_found = int(found)
        if found:
            prov_deposit.quality = quality
    
    db.commit()
    
    return {
        "success": True,
        "found": found,
        "quality": quality,
        "cost": vorkommen.suchkosten_mips,
        "mips_remaining": province.mips
    }

class WorkerModeRequest(BaseModel):
    worker_mode: str

@router.get("/{province_id}/settings")
def get_province_settings(province_id: int, db: Session = Depends(get_db)):
    from app.sammler_jaeger_logic import get_idle_workers
    province = db.query(Province).filter(Province.id == province_id).first()
    if not province:
        raise HTTPException(status_code=404, detail="Province not found")
    
    from app.models import ProvinceSettings
    settings = db.query(ProvinceSettings).filter(
        ProvinceSettings.province_id == province_id
    ).first()
    
    if not settings:
        settings = ProvinceSettings(province_id=province_id, worker_mode="idle")
        db.add(settings)
        db.commit()
    
    idle_workers = get_idle_workers(db, province_id)
    
    return {
        "province_id": province_id,
        "worker_mode": settings.worker_mode,
        "feiertag_active": bool(settings.feiertag_active),
        "feiertag_expires_at": settings.feiertag_expires_at.isoformat() if settings.feiertag_expires_at else None,
        "idle_workers": idle_workers
    }

@router.post("/{province_id}/settings")
def set_worker_mode(province_id: int, request: WorkerModeRequest, db: Session = Depends(get_db)):
    province = db.query(Province).filter(Province.id == province_id).first()
    if not province:
        raise HTTPException(status_code=404, detail="Province not found")
    
    if request.worker_mode not in ["idle", "sammeln", "jagen"]:
        raise HTTPException(status_code=400, detail="Invalid worker_mode. Use: idle, sammeln, or jagen")
    
    from app.models import ProvinceSettings
    settings = db.query(ProvinceSettings).filter(
        ProvinceSettings.province_id == province_id
    ).first()
    
    if not settings:
        settings = ProvinceSettings(province_id=province_id)
        db.add(settings)
    
    settings.worker_mode = request.worker_mode
    db.commit()
    
    return {
        "success": True,
        "worker_mode": settings.worker_mode
    }

@router.post("/{province_id}/feiertag")
def activate_feiertag(province_id: int, db: Session = Depends(get_db)):
    from app.sammler_jaeger_logic import apply_feiertag
    result = apply_feiertag(db, province_id)
    
    if not result:
        raise HTTPException(status_code=400, detail="Feiertag already active or province not found")
    
    return result

@router.get("/{province_id}/settings/loot-preview")
def get_loot_preview(province_id: int, db: Session = Depends(get_db)):
    from app.sammler_jaeger_logic import get_loot_preview as do_get_loot_preview
    preview = do_get_loot_preview(db, province_id)
    
    if not preview:
        raise HTTPException(status_code=404, detail="Province not found")
    
    return preview
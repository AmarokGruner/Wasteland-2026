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

class MilitaryTrainRequest(BaseModel):
    unit_type: str
    count: int

class MilitaryDismissRequest(BaseModel):
    count: int

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


@router.get("/{province_id}/coast")
def get_province_coast(province_id: int, db: Session = Depends(get_db)):
    from app.road_logic import is_coastal_position
    
    province = db.query(Province).filter(Province.id == province_id).first()
    if not province:
        raise HTTPException(status_code=404, detail="Province not found")
    
    terrain = province.terrain or ""
    has_ocean_border = "Ozean" in terrain or "Wasser" in terrain
    
    coast_fields = []
    for x in range(province.fields_total):
        for y in range(province.fields_total):
            if is_coastal_position(db, province_id, x, y):
                coast_fields.append({"x": x, "y": y})
    
    return {
        "province_id": province_id,
        "has_ocean_border": has_ocean_border,
        "sea_access": province.sea_access,
        "coast_field_count": len(coast_fields),
        "coast_fields": coast_fields[:20]  # Limit for response size
    }

@router.post("/{province_id}/irrigate")
def irrigate_province(province_id: int, request: IrrigateRequest, db: Session = Depends(get_db)):
    from app.climate_logic import irrigate_province
    result = irrigate_province(db, province_id, request.water_amount)
    return result

@router.get("/{province_id}/military/status")
def get_military_status(province_id: int, db: Session = Depends(get_db)):
    """Get military status of a province"""
    from app.military_logic import get_military_status
    status = get_military_status(db, province_id)
    if not status:
        raise HTTPException(status_code=404, detail="Province not found")
    return status

@router.post("/{province_id}/military/train")
def train_military(province_id: int, request: MilitaryTrainRequest, db: Session = Depends(get_db)):
    """Train new units in a province"""
    from app.military_logic import train_units
    try:
        unit = train_units(db, province_id, request.unit_type, request.count)
        return {"success": True, "unit_id": unit.id, "unit_count": unit.count, "type": unit.type}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/{province_id}/military/recruit")
def recruit_military(province_id: int, request: MilitaryTrainRequest, db: Session = Depends(get_db)):
    """
    Recruit new military units in a province.

    This endpoint accepts the same payload as the train endpoint and uses the
    same underlying logic to create new units. It returns a success message
    along with details about the recruited units.

    Args:
        province_id: The ID of the province where recruitment takes place.
        request: The request payload containing unit_type and count.
        db: Database session dependency.

    Returns:
        A JSON response indicating success and providing details about the recruited units.
    """
    from app.military_logic import train_units
    try:
        unit = train_units(db, province_id, request.unit_type, request.count)
        return {"success": True, "unit_id": unit.id, "unit_count": unit.count, "type": unit.type}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/{province_id}/military/dismiss")
def dismiss_military(province_id: int, request: MilitaryDismissRequest, db: Session = Depends(get_db)):
    """Dismiss military units and return them to population"""
    from app.military_logic import dismiss_units
    try:
        unit = dismiss_units(db, province_id, request.count)
        return {"success": True, "remaining_count": unit.count}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/{province_id}/bunker")
def get_bunker_status(province_id: int, db: Session = Depends(get_db)):
    """Get bunker status of a province"""
    province = db.query(Province).filter(Province.id == province_id).first()
    if not province:
        raise HTTPException(status_code=404, detail="Province not found")
        
    return {
        "province_id": province.id,
        "has_bunker": bool(province.has_bunker),
        "is_bunker_province": bool(province.is_bunker_province),
        "defense_bonus": province.bunker_defense_bonus if province.has_bunker else 1.0,
        "tech_contribution": 2 if province.has_bunker else 0
    }

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

class TaxSettingsRequest(BaseModel):
    tax_rate: int = None
    lohn_rate: float = None
    sold_rate: float = None
    rente_rate: float = None
    state_transfer_pct: int = None

class TransferRequest(BaseModel):
    amount: float
    to: str

@router.get("/{province_id}/finance")
def get_province_finance(province_id: int, db: Session = Depends(get_db)):
    from app.finance_logic import get_finance_info
    info = get_finance_info(db, province_id)
    
    if not info:
        raise HTTPException(status_code=404, detail="Province not found")
    
    return info

@router.post("/{province_id}/tax-settings")
def set_tax_settings(province_id: int, request: TaxSettingsRequest, db: Session = Depends(get_db)):
    from app.finance_logic import update_tax_settings
    
    result = update_tax_settings(
        db, province_id,
        tax_rate=request.tax_rate,
        lohn_rate=request.lohn_rate,
        sold_rate=request.sold_rate,
        rente_rate=request.rente_rate,
        state_transfer_pct=request.state_transfer_pct
    )
    
    if not result.get("success"):
        raise HTTPException(status_code=400, detail=result.get("error", "Unknown error"))
    
    return result

@router.post("/{province_id}/finance/transfer")
def transfer_funds(province_id: int, request: TransferRequest, db: Session = Depends(get_db)):
    from app.finance_logic import transfer_money

    result = transfer_money(db, province_id, request.amount, request.to)

    if not result.get("success"):
        raise HTTPException(status_code=400, detail=result.get("error", "Transfer failed"))

    return result


# ========== TRADE ROUTES ENDPOINTS ==========

class CreateTradeRouteRequest(BaseModel):
    destination_id: int
    cargo_outbound: dict  # {resource_id: amount}
    settler_count: int
    karren_count: int

class LoadCargoRequest(BaseModel):
    cargo: dict  # {resource_id: amount}

class TradeAtDestinationRequest(BaseModel):
    cargo_return: dict = {}  # {resource_id: amount}

@router.get("/{province_id}/units")
def get_province_units(province_id: int, db: Session = Depends(get_db)):
    """Get all units in province including Handelskarren and Siedler"""
    from app.models import ProvinceUnit, UnitType, TradeRoute, PopulationCohort

    province = db.query(Province).filter(Province.id == province_id).first()
    if not province:
        raise HTTPException(status_code=404, detail="Province not found")

    units = db.query(ProvinceUnit).filter(ProvinceUnit.province_id == province_id).all()

    units_data = []
    for unit in units:
        unit_type = db.query(UnitType).filter(UnitType.id == unit.einheiten_typ_id).first()
        units_data.append({
            "id": unit.id,
            "type_id": unit.einheiten_typ_id,
            "type_name": unit_type.name if unit_type else "",
            "count": unit.count,
            "status": unit.status,
            "geschwindigkeit": unit_type.geschwindigkeit if unit_type else 0,
            "transport_capacity": unit_type.transport_land if unit_type else 0
        })

    # Get eligible settlers (tick_age 4-5)
    from app.trade_route_logic import get_eligible_settlers
    eligible_settlers = get_eligible_settlers(db, province_id)

    # Get all active trade routes
    routes = db.query(TradeRoute).filter(
        (TradeRoute.owner_province_id == province_id) | (TradeRoute.destination_province_id == province_id)
    ).all()

    routes_data = []
    for route in routes:
        routes_data.append({
            "id": route.id,
            "owner_province_id": route.owner_province_id,
            "destination_province_id": route.destination_province_id,
            "status": route.status,
            "travel_ticks_remaining": route.travel_ticks_remaining,
            "total_travel_ticks": route.total_travel_ticks,
            "settler_count": route.settler_count,
            "karren_count": route.karren_count,
            "cargo_outbound": route.cargo_outbound_json,
            "cargo_return": route.cargo_return_json
        })

    return {
        "province_id": province_id,
        "units": units_data,
        "eligible_settlers": eligible_settlers,
        "routes": routes_data
    }

@router.post("/{province_id}/trade-route/create")
def create_trade_route_endpoint(province_id: int, request: CreateTradeRouteRequest, db: Session = Depends(get_db)):
    """Create a new trade route"""
    from app.trade_route_logic import create_trade_route

    try:
        route = create_trade_route(
            db,
            province_id,
            request.destination_id,
            request.cargo_outbound,
            request.settler_count,
            request.karren_count
        )
        return {
            "success": True,
            "route_id": route.id,
            "status": route.status,
            "message": f"Trade route created to province {request.destination_id}"
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/{province_id}/trade-route/{route_id}/load")
def load_cargo_endpoint(province_id: int, route_id: int, request: LoadCargoRequest, db: Session = Depends(get_db)):
    """Load additional cargo to a trade route"""
    from app.trade_route_logic import load_cargo

    try:
        route = load_cargo(db, route_id, request.cargo)
        return {
            "success": True,
            "route_id": route.id,
            "cargo_outbound": route.cargo_outbound_json
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/{province_id}/trade-route/{route_id}/depart")
def depart_route_endpoint(province_id: int, route_id: int, db: Session = Depends(get_db)):
    """Depart the trade route (start traveling)"""
    from app.trade_route_logic import depart_route

    try:
        route = depart_route(db, route_id)
        return {
            "success": True,
            "route_id": route.id,
            "status": route.status,
            "travel_ticks": route.travel_ticks_remaining,
            "message": f"Trade route departed, will arrive in {route.travel_ticks_remaining} ticks"
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/{province_id}/trade-route/{route_id}/status")
def get_route_status(province_id: int, route_id: int, db: Session = Depends(get_db)):
    """Get status of a specific trade route"""
    from app.models import TradeRoute

    route = db.query(TradeRoute).filter(TradeRoute.id == route_id).first()
    if not route:
        raise HTTPException(status_code=404, detail="Trade route not found")

    import json
    return {
        "route_id": route.id,
        "owner_province_id": route.owner_province_id,
        "destination_province_id": route.destination_province_id,
        "status": route.status,
        "travel_ticks_remaining": route.travel_ticks_remaining,
        "total_travel_ticks": route.total_travel_ticks,
        "settler_count": route.settler_count,
        "karren_count": route.karren_count,
        "cargo_outbound": json.loads(route.cargo_outbound_json),
        "cargo_return": json.loads(route.cargo_return_json)
    }

@router.post("/{province_id}/trade-route/{route_id}/trade")
def trade_at_destination_endpoint(province_id: int, route_id: int, request: TradeAtDestinationRequest, db: Session = Depends(get_db)):
    """Execute trade at destination and start return journey"""
    from app.trade_route_logic import execute_trade_at_destination

    try:
        route = execute_trade_at_destination(db, route_id, request.cargo_return)
        return {
            "success": True,
            "route_id": route.id,
            "status": route.status,
            "travel_ticks": route.travel_ticks_remaining,
            "message": f"Trade completed, returning home in {route.travel_ticks_remaining} ticks"
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


class SozialesSettingsRequest(BaseModel):
    kindergeld_rate: float
    rente_rate: float


@router.get("/{province_id}/population")
def get_province_population(province_id: int, db: Session = Depends(get_db)):
    """Get population summary with age groups"""
    from app.population_logic import get_population_summary
    
    province = db.query(Province).filter(Province.id == province_id).first()
    if not province:
        raise HTTPException(status_code=404, detail="Province not found")
    
    summary = get_population_summary(db, province_id)
    return summary


@router.get("/{province_id}/population/forecast")
def get_population_forecast(province_id: int, ticks: int = 5, db: Session = Depends(get_db)):
    """Get projected population evolution"""
    from app.population_logic import get_population_forecast
    
    province = db.query(Province).filter(Province.id == province_id).first()
    if not province:
        raise HTTPException(status_code=404, detail="Province not found")
    
    ticks = max(1, min(30, ticks))
    forecast = get_population_forecast(db, province_id, ticks)
    
    return {"province_id": province_id, "ticks_requested": ticks, "forecast": forecast}


@router.post("/{province_id}/settings/soziales")
def update_soziale_settings(province_id: int, request: SozialesSettingsRequest, db: Session = Depends(get_db)):
    """Update kindergeld and rente rates"""
    from app.population_logic import update_soziale_settings
    
    province = db.query(Province).filter(Province.id == province_id).first()
    if not province:
        raise HTTPException(status_code=404, detail="Province not found")
    
    result = update_soziale_settings(
        db, 
        province_id, 
        kindergeld_rate=request.kindergeld_rate,
        rente_rate=request.rente_rate
    )
    
    return {
        "success": True,
        "province_id": province_id,
        "kindergeld_rate": result["kindergeld_rate"],
        "rente_rate": result["rente_rate"]
    }


@router.get("/{province_id}/kultur")
def get_province_kultur(province_id: int, db: Session = Depends(get_db)):
    """Get culture points and influence data for province"""
    from app.kultur_bildung_logic import get_kultur_influence_data
    
    province = db.query(Province).filter(Province.id == province_id).first()
    if not province:
        raise HTTPException(status_code=404, detail="Province not found")
    
    kultur_data = get_kultur_influence_data(db, province_id)
    
    return {
        "province_id": province_id,
        "kulturpunkte_current": province.kulturpunkte,
        "kultureinfluss_total": kultur_data.get("kultureinfluss_total", 0),
        "kulturpunkte_daily": kultur_data.get("kulturpunkte_daily", 0),
        "can_annex_field": kultur_data.get("can_annex_field", False),
        "progress_percent": kultur_data.get("progress_percent", 0),
        "next_annex_at": kultur_data.get("next_annex_at", 100)
    }


class CreateExpeditionRequest(BaseModel):
    destination_province_id: int
    settler_count: int
    karren_count: int
    cargo: dict


@router.post("/{province_id}/expedition/create")
def create_expedition(province_id: int, request: CreateExpeditionRequest, db: Session = Depends(get_db)):
    """Create a new Siedler expedition to colonize a province"""
    from app.siedler_logic import create_siedler_expedition
    
    try:
        expedition = create_siedler_expedition(
            db,
            province_id,
            request.destination_province_id,
            request.settler_count,
            request.karren_count,
            request.cargo
        )
        return {
            "success": True,
            "expedition_id": expedition.id,
            "status": expedition.status,
            "message": f"Expedition created to province {request.destination_province_id}"
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/{province_id}/expedition/{expedition_id}/depart")
def depart_expedition(province_id: int, expedition_id: int, db: Session = Depends(get_db)):
    """Depart the expedition (start traveling)"""
    from app.siedler_logic import depart_expedition
    
    try:
        expedition = depart_expedition(db, expedition_id)
        return {
            "success": True,
            "expedition_id": expedition.id,
            "status": expedition.status,
            "travel_ticks_remaining": expedition.travel_ticks_remaining,
            "message": f"Expedition departed, will arrive in {expedition.travel_ticks_remaining} ticks"
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/{province_id}/expedition/{expedition_id}/status")
def get_expedition_status(province_id: int, expedition_id: int, db: Session = Depends(get_db)):
    """Get status of a specific expedition"""
    from app.models import SiedlerExpedition
    
    expedition = db.query(SiedlerExpedition).filter(
        SiedlerExpedition.id == expedition_id,
        (SiedlerExpedition.origin_province_id == province_id) | 
        (SiedlerExpedition.destination_province_id == province_id)
    ).first()
    
    if not expedition:
        raise HTTPException(status_code=404, detail="Expedition not found")
    
    import json
    return {
        "expedition_id": expedition.id,
        "origin_province_id": expedition.origin_province_id,
        "destination_province_id": expedition.destination_province_id,
        "status": expedition.status,
        "travel_ticks_remaining": expedition.travel_ticks_remaining,
        "total_travel_ticks": expedition.total_travel_ticks,
        "settler_count": expedition.settler_count,
        "karren_count": expedition.karren_count,
        "cargo": json.loads(expedition.cargo_json),
        "progress_percent": 0 if expedition.total_travel_ticks == 0 else 
            int((1 - expedition.travel_ticks_remaining / expedition.total_travel_ticks) * 100)
    }


@router.get("/{province_id}/expeditions")
def get_province_expeditions(province_id: int, db: Session = Depends(get_db)):
    """Get all expeditions from/to a province"""
    from app.models import SiedlerExpedition
    
    expeditions = db.query(SiedlerExpedition).filter(
        (SiedlerExpedition.origin_province_id == province_id) |
        (SiedlerExpedition.destination_province_id == province_id)
    ).all()
    
    result = []
    for e in expeditions:
        import json
        result.append({
            "expedition_id": e.id,
            "origin_province_id": e.origin_province_id,
            "destination_province_id": e.destination_province_id,
            "status": e.status,
            "travel_ticks_remaining": e.travel_ticks_remaining,
            "settler_count": e.settler_count,
            "karren_count": e.karren_count
        })
    
    return {
        "province_id": province_id,
        "expeditions": result
    }
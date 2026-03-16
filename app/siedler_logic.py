import json
import math
from sqlalchemy.orm import Session
from .models import (
    Province, ProvinceUnit, UnitType, SiedlerExpedition,
    ProvinceLager, Player, PopulationCohort, GameLog, Resource
)
from .trade_route_logic import get_eligible_settlers, deduct_eligible_settlers


MIN_FOUNDING_CARGO = {
    "Bauholz": 50,
    "Stein": 30,
    "Notrationen": 20
}

KULTUR_BONUS = 0.8


def get_unit_type_by_name(db: Session, name: str):
    return db.query(UnitType).filter(UnitType.name == name).first()


def get_unit_type_by_id(db: Session, unit_type_id: int):
    return db.query(UnitType).filter(UnitType.id == unit_type_id).first()


def get_distance(db: Session, origin_id: int, dest_id: int) -> float:
    origin = db.query(Province).filter(Province.id == origin_id).first()
    dest = db.query(Province).filter(Province.id == dest_id).first()
    if not origin or not dest:
        raise ValueError("Invalid province ids for distance calculation")
    dx = origin.world_x - dest.world_x
    dy = origin.world_y - dest.world_y
    return math.sqrt(dx * dx + dy * dy)


def log_game_event(db: Session, province_id: int, event_type: str, message: str, details: dict = None):
    log_entry = GameLog(
        province_id=province_id,
        event_type=event_type,
        message=message,
        details_json=json.dumps(details or {})
    )
    db.add(log_entry)
    db.commit()


def get_colonizable_provinces(db: Session, player_id: int):
    """Get all provinces that can be colonized by a player"""
    provinces = db.query(Province).filter(
        Province.player_id.isnot(None)
    ).all()
    
    result = []
    for p in provinces:
        has_kulturbonus = p.kultureinfluss_owner_id == player_id
        result.append({
            "province_id": p.id,
            "name": p.name or f"Province_{p.id}",
            "world_x": p.world_x,
            "world_y": p.world_y,
            "terrain": p.terrain,
            "owner_id": p.player_id,
            "kultureinfluss_owner_id": p.kultureinfluss_owner_id,
            "has_kulturbonus": has_kulturbonus
        })
    
    unowned = db.query(Province).filter(Province.player_id == None).all()
    for p in unowned:
        result.append({
            "province_id": p.id,
            "name": p.name or f"Province_{p.id}",
            "world_x": p.world_x,
            "world_y": p.world_y,
            "terrain": p.terrain,
            "owner_id": None,
            "kultureinfluss_owner_id": p.kultureinfluss_owner_id,
            "has_kulturbonus": False
        })
    
    return result


def validate_founding_cargo(db: Session, province_id: int, cargo: dict) -> tuple[bool, list[str]]:
    """Validate founding cargo meets minimum requirements. Returns (valid, missing_resources)"""
    resource_map = {}
    resources = db.query(Resource).all()
    for r in resources:
        resource_map[r.name.lower()] = r.id
    
    missing = []
    for res_name, min_amount in MIN_FOUNDING_CARGO.items():
        if res_name.lower() not in resource_map:
            missing.append(res_name)
            continue
        
        res_id = resource_map[res_name.lower()]
        available = cargo.get(str(res_id), 0)
        if available < min_amount:
            missing.append(f"{res_name} (need {min_amount}, have {available})")
    
    return len(missing) == 0, missing


def apply_kultur_bonus(cargo: dict) -> dict:
    """Apply 20% cost reduction for own-culture colonization"""
    return {k: int(v * KULTUR_BONUS) for k, v in cargo.items()}


def create_siedler_expedition(
    db: Session,
    origin_province_id: int,
    destination_province_id: int,
    settler_count: int,
    karren_count: int,
    cargo: dict
):
    origin = db.query(Province).filter(Province.id == origin_province_id).first()
    dest = db.query(Province).filter(Province.id == destination_province_id).first()
    
    if not origin or not dest:
        raise ValueError("Origin or destination province not found")
    
    player = db.query(Player).filter(Player.id == origin.player_id).first()
    if not player:
        raise ValueError("Owner player not found")
    
    eligible_count = get_eligible_settlers(db, origin_province_id)
    if eligible_count < settler_count:
        raise ValueError(f"NO_ELIGIBLE_SETTLERS: Need {settler_count}, but only {eligible_count} settlers aged 20-25 available")
    
    if dest.player_id is not None and dest.kultureinfluss_owner_id != player.id:
        raise ValueError("PROVINCE_OCCUPIED: Destination must be unowned or have your culture influence")
    
    has_kulturbonus = dest.kultureinfluss_owner_id == player.id
    required_cargo = MIN_FOUNDING_CARGO.copy()
    if has_kulturbonus:
        for k in required_cargo:
            required_cargo[k] = int(required_cargo[k] * KULTUR_BONUS)
    
    resource_map = {}
    resources = db.query(Resource).all()
    for r in resources:
        resource_map[r.name.lower()] = r.id
    
    valid, missing = validate_founding_cargo(db, origin_province_id, cargo)
    if not valid:
        raise ValueError(f"INSUFFICIENT_FOUNDING_CARGO: Missing {', '.join(missing)}")
    
    karren_type = get_unit_type_by_name(db, "Handelskarren")
    if not karren_type:
        raise ValueError("Handelskarren unit type not defined")
    
    karren_units = db.query(ProvinceUnit).filter(
        ProvinceUnit.provinz_id == origin_province_id,
        ProvinceUnit.einheiten_typ_id == karren_type.id
    ).first()
    if not karren_units or karren_units.count < karren_count:
        raise ValueError("Not enough Handelskarren in province")
    
    capacity_per_karren = karren_type.transport_land or 100
    total_capacity = capacity_per_karren * karren_count
    total_cargo = sum(cargo.values())
    if total_cargo > total_capacity:
        raise ValueError(f"Cargo ({total_cargo}) exceeds total transport capacity ({total_capacity})")
    
    for res_id, amount in cargo.items():
        lager_item = db.query(ProvinceLager).filter(
            ProvinceLager.provinz_id == origin_province_id,
            ProvinceLager.ressource_id == int(res_id)
        ).first()
        if not lager_item or lager_item.menge < amount:
            raise ValueError(f"Not enough resource {res_id} in storage")
        lager_item.menge -= amount
    
    tick_age_used = deduct_eligible_settlers(db, origin_province_id, settler_count)
    
    karren_units.count -= karren_count
    if karren_units.count == 0:
        db.delete(karren_units)
    
    expedition = SiedlerExpedition(
        owner_id=player.id,
        origin_province_id=origin_province_id,
        destination_province_id=destination_province_id,
        settler_count=settler_count,
        karren_count=karren_count,
        cargo_json=json.dumps(cargo),
        status="preparing",
        settler_tick_age=tick_age_used
    )
    db.add(expedition)
    db.commit()
    db.refresh(expedition)
    
    log_game_event(
        db, origin_province_id, "EXPEDITION_CREATED",
        f"Siedler expedition created to province {destination_province_id} with {karren_count} karren and {settler_count} settlers",
        {"destination_id": destination_province_id, "karren_count": karren_count, "settler_count": settler_count}
    )
    
    return expedition


def depart_expedition(db: Session, expedition_id: int):
    expedition = db.query(SiedlerExpedition).filter(SiedlerExpedition.id == expedition_id).first()
    if not expedition:
        raise ValueError("Expedition not found")
    if expedition.status != "preparing":
        raise ValueError("Can only depart from preparing state")
    
    distance = get_distance(db, expedition.origin_province_id, expedition.destination_province_id)
    
    siedler_type = get_unit_type_by_name(db, "Siedler")
    speed = siedler_type.geschwindigkeit if siedler_type else 1.0
    
    travel_ticks = max(1, int(distance / speed))
    expedition.travel_ticks_remaining = travel_ticks
    expedition.total_travel_ticks = travel_ticks
    expedition.status = "traveling"
    db.commit()
    
    log_game_event(
        db, expedition.origin_province_id, "EXPEDITION_DEPARTED",
        f"Siedler expedition {expedition_id} departed, will arrive in {travel_ticks} ticks",
        {"expedition_id": expedition_id, "destination_province_id": expedition.destination_province_id}
    )
    
    return expedition


def colonize_destination(db: Session, expedition_id: int):
    """Execute colonization when expedition arrives"""
    expedition = db.query(SiedlerExpedition).filter(SiedlerExpedition.id == expedition_id).first()
    if not expedition:
        raise ValueError("Expedition not found")
    if expedition.status != "arrived":
        raise ValueError("Can only colonize when status is 'arrived'")
    
    dest = db.query(Province).filter(Province.id == expedition.destination_province_id).first()
    player = db.query(Player).filter(Player.id == expedition.owner_id).first()
    
    if dest.player_id is not None:
        raise ValueError("PROVINCE_OCCUPIED: Province was colonized by another player")
    
    dest.player_id = expedition.owner_id
    dest.name = f"{player.name}s Kolonie"
    
    cargo = json.loads(expedition.cargo_json)
    for res_id_str, amount in cargo.items():
        res_id = int(res_id_str)
        lager_item = db.query(ProvinceLager).filter(
            ProvinceLager.provinz_id == expedition.destination_province_id,
            ProvinceLager.ressource_id == res_id
        ).first()
        if not lager_item:
            lager_item = ProvinceLager(
                provinz_id=expedition.destination_province_id,
                ressource_id=res_id,
                menge=0
            )
            db.add(lager_item)
        lager_item.menge += amount
    
    cohort = db.query(PopulationCohort).filter(
        PopulationCohort.province_id == expedition.destination_province_id,
        PopulationCohort.tick_age == expedition.settler_tick_age
    ).first()
    if not cohort:
        cohort = PopulationCohort(
            province_id=expedition.destination_province_id,
            tick_age=expedition.settler_tick_age,
            count=expedition.settler_count
        )
        db.add(cohort)
    else:
        cohort.count += expedition.settler_count
    
    siedler_type = get_unit_type_by_name(db, "Siedler")
    siedler_unit = ProvinceUnit(
        province_id=expedition.destination_province_id,
        einheiten_typ_id=siedler_type.id if siedler_type else None,
        count=expedition.settler_count,
        status="idle"
    )
    db.add(siedler_unit)
    
    expedition.status = "colonized"
    db.commit()
    
    log_game_event(
        db, expedition.destination_province_id, "PROVINCE_COLONIZED",
        f"Province {dest.name} colonized by {player.name}",
        {"province_id": dest.id, "owner": player.name, "settler_count": expedition.settler_count}
    )
    
    return dest


def process_expeditions(db: Session):
    """Called every tick to process all active expeditions"""
    expeditions = db.query(SiedlerExpedition).filter(
        SiedlerExpedition.status.in_(["traveling", "arrived"])
    ).all()
    
    for expedition in expeditions:
        if expedition.travel_ticks_remaining > 0:
            expedition.travel_ticks_remaining -= 1
        
        if expedition.travel_ticks_remaining <= 0:
            if expedition.status == "traveling":
                expedition.status = "arrived"
                
                log_game_event(
                    db, expedition.destination_province_id, "EXPEDITION_ARRIVED",
                    f"Siedler expedition from province {expedition.origin_province_id} has arrived",
                    {"origin_province_id": expedition.origin_province_id, "expedition_id": expedition.id}
                )
            
            elif expedition.status == "arrived":
                try:
                    colony = colonize_destination(db, expedition.id)
                    
                    karren_type = get_unit_type_by_name(db, "Handelskarren")
                    if karren_type and expedition.karren_count > 0:
                        karren_units = db.query(ProvinceUnit).filter(
                            ProvinceUnit.provinz_id == expedition.destination_province_id,
                            ProvinceUnit.einheiten_typ_id == karren_type.id
                        ).first()
                        if not karren_units:
                            karren_units = ProvinceUnit(
                                province_id=expedition.destination_province_id,
                                einheiten_typ_id=karren_type.id,
                                count=expedition.karren_count,
                                status="idle"
                            )
                            db.add(karren_units)
                        else:
                            karren_units.count += expedition.karren_count
                    
                except ValueError as e:
                    log_game_event(
                        db, expedition.destination_province_id, "EXPEDITION_FAILED",
                        f"Colonization failed: {str(e)}",
                        {"expedition_id": expedition.id, "error": str(e)}
                    )
    
    db.commit()


def transfer_province(db: Session, province_id: int, from_player_id: int, to_player_id: int):
    """Transfer ownership of a province from one player to another"""
    province = db.query(Province).filter(Province.id == province_id).first()
    if not province:
        raise ValueError("Province not found")
    
    if province.player_id != from_player_id:
        raise ValueError(f"Province {province_id} not owned by player {from_player_id}")
    
    to_player = db.query(Player).filter(Player.id == to_player_id).first()
    if not to_player:
        raise ValueError("Target player not found")
    
    buildings_to_destroy = []
    for building in province.buildings:
        spec = json.loads(building.type.spezial_eigenschaften or "{}")
        if "bunker" in spec:
            buildings_to_destroy.append(building)
    
    for building in buildings_to_destroy:
        db.delete(building)
    
    old_owner = db.query(Player).filter(Player.id == from_player_id).first()
    
    province.player_id = to_player_id
    db.commit()
    
    log_game_event(
        db, province_id, "PROVINCE_TRANSFERRED",
        f"Province transferred from {old_owner.name if old_owner else 'unowned'} to {to_player.name}",
        {"from": from_player_id, "to": to_player_id}
    )
    
    return province
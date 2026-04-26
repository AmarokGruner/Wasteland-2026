from sqlalchemy.orm import Session
from .models import Province, BuildingInstance, BuildingType, Player
import json

def claim_province_with_bunker(db: Session, player_id: int, province_id: int):
    """
    Opens a bunker to claim an unowned province.
    1 bunker per player per world map.
    """
    province = db.query(Province).filter(Province.id == province_id).first()
    if not province:
        raise ValueError("Province not found")
        
    if province.player_id is not None:
        # Check if it belongs to someone (in current implementation player_id 0 or null might be used for unowned)
        # Assuming player_id is required and 0 or None means unowned
        if province.player_id != 0:
             raise ValueError("Province is already owned")

    # require no other bunker opened by same player on this map
    existing_bunker = db.query(Province).filter(
        Province.player_id == player_id,
        Province.is_bunker_province == 1
    ).first()
    if existing_bunker:
        raise ValueError("Player already has a bunker province")

    # Set province ownership
    province.player_id = player_id
    province.is_bunker_province = 1
    province.has_bunker = 1
    province.bunker_defense_bonus = 1.3
    
    # Place Bunker building (baubar=0, indestructible, unique)
    bunker_type = db.query(BuildingType).filter(BuildingType.name == "Bunker").first()
    if not bunker_type:
        # Create Bunker type if it doesn't exist
        bunker_type = BuildingType(
            name="Bunker",
            kategorie="Militär",
            bautyp="Stadt",
            baubar=0,
            spezial_eigenschaften=json.dumps({"techproduktion": 2, "indestructible": True})
        )
        db.add(bunker_type)
        db.flush()

    # Find a free spot for the bunker (usually 0,0 for simplicity if city field)
    # Check if anything is already at 0,0
    existing_b = db.query(BuildingInstance).filter(
        BuildingInstance.provinz_id == province_id,
        BuildingInstance.x == 0,
        BuildingInstance.y == 0
    ).first()
    
    if existing_b:
        # Find another spot
        # In a real grid we would search, but let's assume 0,0 is city center
        pass

    new_bunker = BuildingInstance(
        provinz_id=province_id,
        gebaeude_typ_id=bunker_type.id,
        x=0,
        y=0,
        level=1
    )
    db.add(new_bunker)
    
    # Log event
    from .trade_route_logic import log_game_event
    log_game_event(db, province_id, "BUNKER_OPENED", f"Player {player_id} claimed province {province_id} by opening a bunker.")
    
    db.commit()
    return province

def destroy_bunker(db: Session, province: Province):
    """
    Automatically demolished if province is conquered.
    """
    if not province.has_bunker:
        return
        
    # Find bunker building
    bunker_buildings = db.query(BuildingInstance).join(BuildingType).filter(
        BuildingInstance.provinz_id == province.id,
        BuildingType.name == "Bunker"
    ).all()
    
    for b in bunker_buildings:
        db.delete(b)
    
    province.has_bunker = 0
    province.is_bunker_province = 0
    # Tech production contribution is handled in kultur_bildung_logic by checking buildings
    
    db.commit()

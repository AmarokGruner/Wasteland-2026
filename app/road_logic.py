from sqlalchemy.orm import Session
from app.models import Province, RoadInstance, BuildingType, Player
import json
from collections import deque

def get_adjacent_positions(x: int, y: int) -> list:
    return [
        (x-1, y), (x+1, y),
        (x, y-1), (x, y+1)
    ]

def is_road_network_connected(db: Session, province_id: int) -> list:
    """
    Returns a set of all connected road field positions (x, y) using BFS.
    """
    roads = db.query(RoadInstance).filter(RoadInstance.provinz_id == province_id).all()
    if not roads:
        return set()
    
    road_positions = {(r.x, r.y) for r in roads}
    
    intersections = [pos for pos in road_positions if is_intersection(db, province_id, pos[0], pos[1])]
    
    if not intersections:
        return road_positions
    
    visited = set()
    queue = deque(intersections)
    
    while queue:
        cx, cy = queue.popleft()
        if (cx, cy) in visited:
            continue
        visited.add((cx, cy))
        
        for nx, ny in get_adjacent_positions(cx, cy):
            if (nx, ny) in road_positions:
                props = json.loads(
                    db.query(RoadInstance).filter(
                        RoadInstance.provinz_id == province_id,
                        RoadInstance.x == nx,
                        RoadInstance.y == ny
                    ).first().type.spezial_eigenschaften
                )
                if props.get("wegstufe", 0) > 0:
                    queue.append((nx, ny))
    
    return visited

def is_intersection(db: Session, province_id: int, x: int, y: int) -> bool:
    """
    Checks if a road position is an intersection (has roads in 2+ perpendicular directions).
    """
    road = db.query(RoadInstance).filter(
        RoadInstance.provinz_id == province_id,
        RoadInstance.x == x,
        RoadInstance.y == y
    ).first()
    
    if not road:
        return False
    
    props = json.loads(road.type.spezial_eigenschaften)
    if "wegstufe" not in props:
        return False
    
    adjacent = get_adjacent_positions(x, y)
    
    directions_found = 0
    for ax, ay in adjacent:
        existing = db.query(RoadInstance).filter(
            RoadInstance.provinz_id == province_id,
            RoadInstance.x == ax,
            RoadInstance.y == ay
        ).first()
        
        if existing:
            directions_found += 1
    
    return directions_found >= 2

def can_build_road(db: Session, province_id: int, x: int, y: int) -> tuple:
    """
    Checks if a road can be built at the given position.
    Must connect to existing network (at least one adjacent road or intersection).
    """
    province = db.query(Province).filter(Province.id == province_id).first()
    
    existing_road = db.query(RoadInstance).filter(
        RoadInstance.provinz_id == province_id,
        RoadInstance.x == x,
        RoadInstance.y == y
    ).first()
    
    if existing_road:
        return False, "Position bereits belegt"
    
    adjacent = get_adjacent_positions(x, y)
    has_connection = False
    
    for ax, ay in adjacent:
        existing = db.query(RoadInstance).filter(
            RoadInstance.provinz_id == province_id,
            RoadInstance.x == ax,
            RoadInstance.y == ay
        ).first()
        
        if existing:
            has_connection = True
            break
    
    connected_roads = is_road_network_connected(db, province_id)
    
    if not has_connection and len(connected_roads) > 0:
        return False, "Road muss an existierendes Straßennetz angrenzen"
    
    if has_connection:
        return True, ""
        
    if len(connected_roads) == 0 and has_connection:
        return True, ""
    
    if len(connected_roads) == 0 and not has_connection:
        return False, "Erster Road muss eine Kreuzung sein"
    
    return True, ""

def build_road(db: Session, province_id: int, template_id: int, x: int, y: int) -> dict:
    """
    Builds a road at the given position if allowed.
    Deducts AP based on baukostenmips / 1000 formula from feature docs.
    """
    province = db.query(Province).filter(Province.id == province_id).first()
    template = db.query(BuildingType).filter(BuildingType.id == template_id).first()
    
    if not template:
        return {"success": False, "error": "Building-Template nicht gefunden"}
    
    if template.bautyp not in ["Weg", "Wegkreuzung"]:
        return {"success": False, "error": "Template ist kein Weg oder Kreuzung"}
    
    ok, msg = can_build_road(db, province_id, x, y)
    if not ok:
        return {"success": False, "error": msg}
    
    props = json.loads(template.spezial_eigenschaften)
    wegstufe = props.get("wegstufe", 1)
    
    ap_cost = max(1, template.baukosten_mips // 1000)
    
    if province.arbeitspunkte_current < ap_cost:
        return {"success": False, "error": f"Nicht genügend AP ({province.arbeitspunkte_current}/{ap_cost})"}
    
    new_road = RoadInstance(
        provinz_id=province_id,
        gebaeude_typ_id=template_id,
        x=x,
        y=y
    )
    
    db.add(new_road)
    province.arbeitspunkte_current -= ap_cost
    
    return {
        "success": True,
        "road_id": new_road.id,
        "x": x,
        "y": y,
        "wegstufe": wegstufe,
        "ap_cost": ap_cost,
        "ap_remaining": province.arbeitspunkte_current
    }

def demolish_road(db: Session, road_id: int) -> dict:
    """
    Demolishes a road and refunds 50% of AP.
    """
    road = db.query(RoadInstance).filter(RoadInstance.id == road_id).first()
    
    if not road:
        return {"success": False, "error": "Road nicht gefunden"}
    
    province = road.province
    template = road.type
    
    props = json.loads(template.spezial_eigenschaften)
    wegstufe = props.get("wegstufe", 1)
    
    ap_cost = max(1, template.baukosten_mips // 1000)
    refund_ap = int(ap_cost * 0.5)
    
    if province.arbeitspunkte_current < ap_cost:
        return {"success": False, "error": f"Nicht genügend AP ({province.arbeitspunkte_current}/{ap_cost})"}
    
    province.arbeitspunkte_current -= ap_cost
    province.arbeitspunkte_current += refund_ap
    
    db.delete(road)
    
    return {
        "success": True,
        "ap_cost": ap_cost,
        "refund_ap": refund_ap,
        "ap_remaining": province.arbeitspunkte_current
    }

def auto_build_roads(db: Session, province_id: int, road_type_name: str) -> dict:
    """
    Builds roads using ALL available AP.
    """
    province = db.query(Province).filter(Province.id == province_id).first()
    
    template = db.query(BuildingType).filter(
        BuildingType.name == road_type_name,
        BuildingType.bautyp.in_(["Weg", "Wegkreuzung"])
    ).first()
    
    if not template:
        return {"success": False, "error": f"Kein Weg-Template gefunden: {road_type_name}"}
    
    props = json.loads(template.spezial_eigenschaften)
    wegstufe = props.get("wegstufe", 1)
    
    ap_cost_per_road = max(1, template.baukosten_mips // 1000)
    max_roads = province.arbeitspunkte_current // ap_cost_per_road
    
    if max_roads == 0:
        return {"success": False, "error": f"Nicht genügend AP für einen Road ({province.arbeitspunkte_current}/{ap_cost_per_road})"}
    
    built_count = 0
    
    connected = is_road_network_connected(db, province_id)
    
    possible_positions = []
    existing_roads = {(r.x, r.y) for r in db.query(RoadInstance).filter(RoadInstance.provinz_id == province_id).all()}
    
    for cx, cy in connected:
        for ax, ay in get_adjacent_positions(cx, cy):
            if (ax, ay) not in existing_roads and (ax, ay) not in [(p[0], p[1]) for p in possible_positions]:
                if 0 <= ax < province.fields_total and 0 <= ay < province.fields_total:
                    possible_positions.append((ax, ay))
    
    for x, y in possible_positions[:max_roads]:
        result = build_road(db, province_id, template.id, x, y)
        if result.get("success"):
            built_count += 1
        else:
            break
    
    return {
        "success": True,
        "roads_built": built_count,
        "ap_spent": built_count * ap_cost_per_road,
        "ap_remaining": province.arbeitspunkte_current
    }

def is_coastal_position(db: Session, province_id: int, x: int, y: int) -> bool:
    """
    Checks if a position is on the outer ring of land adjacent to ocean.
    This requires checking if any neighbor is water/ocean terrain.
    """
    province = db.query(Province).filter(Province.id == province_id).first()
    
    is_on_outer_ring = (x == 0 or x == province.fields_total - 1 or 
                        y == 0 or y == province.fields_total - 1)
    
    if not is_on_outer_ring:
        return False
    
    adjacent_water = False
    terrain = province.terrain
    
    if "Wasser" in terrain or "Ozean" in terrain:
        return True
    
    return False
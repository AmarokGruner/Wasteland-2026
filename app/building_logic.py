from sqlalchemy.orm import Session
from app.models import Province, BuildingType, BuildingInstance, ProvinceLager, Resource, Player
from fastapi import HTTPException
import json
from datetime import datetime

def get_lager_dict(db: Session, province_id: int):
    lager = db.query(ProvinceLager).filter(ProvinceLager.provinz_id == province_id).all()
    return {l.ressource_id: l.menge for l in lager}

def deduct_resources(db: Session, province_id: int, requirements: list):
    for req in requirements:
        res_name = req["ressource"]
        amount = req["menge"]
        
        resource = db.query(Resource).filter(Resource.name == res_name).first()
        if not resource:
            continue
            
        lager_entry = db.query(ProvinceLager).filter(
            ProvinceLager.provinz_id == province_id,
            ProvinceLager.ressource_id == resource.id
        ).first()
        
        if lager_entry:
            lager_entry.menge -= amount

def can_build(db: Session, template_id: int, province_id: int, x: int, y: int):
    template = db.query(BuildingType).filter(BuildingType.id == template_id).first()
    province = db.query(Province).filter(Province.id == province_id).first()
    player = db.query(Player).filter(Player.id == province.player_id).first()
    
    if not template or not province:
        return False, "Gebäude-Template oder Provinz nicht gefunden"
        
    # 1. Tech Level Check
    if player.tech_level < template.tech_level:
        return False, f"Tech-Level zu niedrig ({player.tech_level}/{template.tech_level})"
        
    # 2. MIPS Check
    if province.mips < template.baukosten_mips:
        return False, f"Nicht genügend MIPS ({province.mips}/{template.baukosten_mips})"
        
    # 3. Resources Check
    requirements = json.loads(template.rohstoffbedarf_bau)
    lager = get_lager_dict(db, province_id)
    
    for req in requirements:
        res_name = req["ressource"]
        amount = req["menge"]
        resource = db.query(Resource).filter(Resource.name == res_name).first()
        if not resource:
             return False, f"Ressource {res_name} nicht in Datenbank definiert"
        if lager.get(resource.id, 0) < amount:
            return False, f"Nicht genügend {res_name} ({int(lager.get(resource.id, 0))}/{amount})"

    # 4. Position/Bautyp Check
    # Simplified for now: check if already building at this position?
    existing = db.query(BuildingInstance).filter(
        BuildingInstance.provinz_id == province_id,
        BuildingInstance.x == x,
        BuildingInstance.y == y
    ).first()
    if existing:
        return False, "Position bereits belegt"
        
    # 5. Unique Check
    if template.unique_gebaeude:
        instance_count = db.query(BuildingInstance).filter(
            BuildingInstance.provinz_id == province_id,
            BuildingInstance.gebaeude_typ_id == template_id
        ).count()
        if instance_count > 0:
            return False, "Dieses Gebäude kann nur einmal pro Provinz gebaut werden."

    # 6. Stadtausbau Check
    if template.bautyp == "Stadtausbau":
        # Only one Stadtausbau active? Actually, they replace each other.
        pass

    return True, ""

def build_building(db: Session, template_id: int, province_id: int, x: int, y: int):
    ok, msg = can_build(db, template_id, province_id, x, y)
    if not ok:
        raise HTTPException(status_code=400, detail=msg)
        
    template = db.query(BuildingType).filter(BuildingType.id == template_id).first()
    province = db.query(Province).filter(Province.id == province_id).first()
    
    # Deduct MIPS
    province.mips -= template.baukosten_mips
    
    # Deduct Resources
    requirements = json.loads(template.rohstoffbedarf_bau)
    deduct_resources(db, province_id, requirements)
    
    # Create Instance
    new_instance = BuildingInstance(
        provinz_id=province_id,
        gebaeude_typ_id=template_id,
        x=x,
        y=y,
        level=1,
        built_at=datetime.now()
    )
    db.add(new_instance)
    
    # Special Logic: Stadtausbau
    if template.bautyp == "Stadtausbau":
        apply_city_expansion(db, province, template)
        
    db.commit()
    
    return {
        "success": True,
        "new_instance": {
            "id": new_instance.id,
            "template_id": new_instance.gebaeude_typ_id,
            "level": new_instance.level,
            "x": new_instance.x,
            "y": new_instance.y
        },
        "ap_remaining": province.arbeitspunkte_current,
        "mips_remaining": province.mips
    }

def apply_city_expansion(db: Session, province: Province, template: BuildingType):
    props = json.loads(template.spezial_eigenschaften)
    
    # upgrade_province_size logic from spec
    kultur_delta = props.get("kulturpunkte", 0)
    size_delta = props.get("provinzgroesse", 0)
    
    province.kulturpunkte += kultur_delta
    # spec says size_level (1-7), but provinzgroesse_delta affects fields
    # Let's assume size_level increases by 1 if it's a Stadtausbau
    province.size_level += 1
    province.fields_city += size_delta
    # also fields_total? spec says "upgrade size_level... each upgrade fields_city += delta"
    
    # remove previous Stadtausbau instances? 
    # Usually Stadtausbau represents the current level.
    # We should probably delete old Stadtausbau instances to keep only one.
    old_expansions = db.query(BuildingInstance).join(BuildingType).filter(
        BuildingInstance.provinz_id == province.id,
        BuildingType.bautyp == "Stadtausbau",
        BuildingInstance.gebaeude_typ_id != template.id
    ).all()
    for old in old_expansions:
        db.delete(old)

def upgrade_building(db: Session, instance_id: int):
    instance = db.query(BuildingInstance).filter(BuildingInstance.id == instance_id).first()
    if not instance:
        raise HTTPException(status_code=404, detail="Gebäudeinstanz nicht gefunden")
        
    template = instance.type
    if not template.ausbaubar:
        raise HTTPException(status_code=400, detail="Dieses Gebäude ist nicht ausbaubar")
        
    if instance.level >= 10:
        raise HTTPException(status_code=400, detail="Maximale Stufe (10) bereits erreicht")
        
    province = instance.province
    
    # 1. Scaling MIPS costs: ausbaukosten_mips * current_level
    current_mips_costs = template.ausbaukosten_mips * instance.level
    if province.mips < current_mips_costs:
        raise HTTPException(status_code=400, detail=f"Nicht genügend MIPS für Upgrade ({province.mips}/{current_mips_costs})")
        
    # 2. Resource costs: rohstoffgrundbedarf_ausbau
    # Usually these also scale or are fixed per level?
    # Spec says "deduct ausbaukostenmips + upgrade_resources"
    try:
        upgrade_requirements = json.loads(template.rohstoffgrundbedarf_ausbau)
    except:
        upgrade_requirements = []
        
    lager = get_lager_dict(db, province.id)
    for req in upgrade_requirements:
        res_name = req["ressource"]
        amount = req["menge"] # Should maybe scale with level? amount * instance.level?
        resource = db.query(Resource).filter(Resource.name == res_name).first()
        if resource and lager.get(resource.id, 0) < amount:
            return False, f"Nicht genügend {res_name} ({int(lager.get(resource.id, 0))}/{amount})"

    # Deduct costs
    province.mips -= current_mips_costs
    deduct_resources(db, province.id, upgrade_requirements)
    
    instance.level += 1
    
    # ON UPGRADE: scaled workers and living space (linear per spec)
    # This is usually handled in provincial consumption/tick logic, 
    # but we can log that instance.level changed.
    
def get_ap_cost(template: BuildingType):
    # Rule from 05_feature_wege_arbeit.md: baukostenmips / 1000 AP
    cost = template.baukosten_mips // 1000
    return max(1, cost)

def can_demolish(db: Session, instance_id: int):
    instance = db.query(BuildingInstance).filter(BuildingInstance.id == instance_id).first()
    if not instance:
        return False, "Gebäudeinstanz nicht gefunden", 0
        
    template = instance.type
    province = instance.province
    
    # 1. Stadtausbau Check
    if template.bautyp == "Stadtausbau":
        return False, "Stadtausbau-Gebäude können nicht abgerissen werden", 0
        
    # 2. Bunker Check
    if template.unique_gebaeude and template.name == "Bunker":
         return False, "Der Bunker kann nicht abgerissen werden", 0
         
    # 3. AP Check
    ap_cost = get_ap_cost(template)
    if province.arbeitspunkte_current < ap_cost:
        return False, f"Nicht genügend Arbeitspunkte ({province.arbeitspunkte_current}/{ap_cost})", ap_cost

    return True, "", ap_cost

def get_ap_cost(template: BuildingType) -> int:
    """Returns the AP cost for constructing a building."""
    # Simplified: return 10 for all for now, or use a property if added
    return 10

def demolish_building(db: Session, instance_id: int):
    ok, msg, ap_cost = can_demolish(db, instance_id)
    if not ok:
        raise HTTPException(status_code=400, detail=msg)
        
    instance = db.query(BuildingInstance).filter(BuildingInstance.id == instance_id).first()
    template = instance.type
    province = instance.province
    
    # Calculate Refund (50% of rohstoffbedarf_bau)
    # Note: Ruins would need 25%, but we don't have a 'ruin' flag yet. 
    # Logic from spec: refund = rohstoffbedarfbau * 0.5
    refund_ratio = 0.5
    # TODO: Check for ruins if implemented later
    
    requirements = json.loads(template.rohstoffbedarf_bau)
    refunded_resources = []
    
    for req in requirements:
        res_name = req["ressource"]
        amount = int(req["menge"] * refund_ratio)
        if amount <= 0:
            continue
            
        resource = db.query(Resource).filter(Resource.name == res_name).first()
        if not resource:
            continue
            
        lager_entry = db.query(ProvinceLager).filter(
            ProvinceLager.provinz_id == province.id,
            ProvinceLager.ressource_id == resource.id
        ).first()
        
        if not lager_entry:
            lager_entry = ProvinceLager(provinz_id=province.id, ressource_id=resource.id, menge=0)
            db.add(lager_entry)
            
        lager_entry.menge += amount
        refunded_resources.append({"ressource": res_name, "menge": amount})

    # Deduct AP
    province.arbeitspunkte_current -= ap_cost
    
    # Remove Instance
    field_id = instance.x # In citytiles_view, x is used as field_id/position
    db.delete(instance)
    db.commit()
    
    return {
        "success": True,
        "refunded_resources": refunded_resources,
        "ap_cost": ap_cost,
        "ap_remaining": province.arbeitspunkte_current,
        "field_id": field_id
    }

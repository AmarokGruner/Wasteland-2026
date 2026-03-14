from sqlalchemy.orm import Session
import random
from datetime import datetime, timedelta
from app.models import Province, ProvinceSettings, SammelLoot, JagdLoot, Resource, ProvinceLager

MATERIAL_LOOT = [
    ("Bauholz", 2.0, 0.5, 2.0),
    ("Stein", 1.0, 0.3, 1.5),
    ("Kies", 1.0, 0.2, 1.2),
    ("Notrationen", 0.5, 0.0, 0.8),
    ("Stroh", 0.5, 0.0, 1.0),
]

FORAGE_LOOT = [
    ("Beeren", 0.4, 0.0, 0.8, ["Wald", "Grünland", "Dschungel"]),
    ("Pilze", 0.3, 0.0, 0.7, ["Wald", "Sumpf", "Dschungel"]),
    ("Gewürze", 0.1, 0.0, 0.4, ["Savanne", "Grünland", "Dschungel"]),
    ("Früchte", 0.2, 0.0, 0.6, ["Tropen", "Dschungel", "Wald"]),
]

FOREST_CROPS = ["Getreide", "Kartoffeln"]
WALD_CROPS = ["Pilze", "Beeren"]
SAVANNE_CROPS = ["Hirse"]

def get_terrain_possible_crops(terrain: str) -> list:
    terrain_map = {
        "Grasland": FOREST_CROPS,
        "Wald": WALD_CROPS,
        "Steppe": FOREST_CROPS,
        "Savanne": SAVANNE_CROPS,
        "Dschungel": ["Pilze", "Beeren", "Gewürze"],
        "Tropen": ["Früchte", "Gewürze"],
    }
    return terrain_map.get(terrain, [])

def get_idle_workers(db: Session, province_id: int) -> int:
    province = db.query(Province).filter(Province.id == province_id).first()
    if not province:
        return 0
    
    from app.models import BuildingInstance
    total_workers = sum(b.type.arbeiter for b in province.buildings)
    
    return max(0, province.population - total_workers)

def apply_feiertag(db: Session, province_id: int):
    province = db.query(Province).filter(Province.id == province_id).first()
    if not province:
        return None
    
    settings = db.query(ProvinceSettings).filter(
        ProvinceSettings.province_id == province_id
    ).first()
    
    if not settings:
        settings = ProvinceSettings(province_id=province_id)
        db.add(settings)
    
    if settings.feiertag_active:
        return None
    
    moral_bonus = 5
    province.moral += moral_bonus
    
    idle_workers = get_idle_workers(db, province_id)
    lohn_rate = 0.1
    provinz_konto_cost = idle_workers * lohn_rate
    
    province.mips -= provinz_konto_cost
    
    settings.feiertag_active = 1
    settings.feiertag_expires_at = datetime.now() + timedelta(hours=24)
    
    db.commit()
    
    return {
        "success": True,
        "moral_bonus": moral_bonus,
        "cost_mips": provinz_konto_cost,
        "feiertag_expires_at": settings.feiertag_expires_at.isoformat()
    }

def get_sammeln_loot(db: Session, province_id: int):
    province = db.query(Province).filter(Province.id == province_id).first()
    if not province:
        return None
    
    settings = db.query(ProvinceSettings).filter(
        ProvinceSettings.province_id == province_id
    ).first()
    
    if not settings:
        settings = ProvinceSettings(province_id=province_id)
        db.add(settings)
    
    if not settings.feiertag_active:
        idle_workers = get_idle_workers(db, province_id)
    else:
        idle_workers = 0
    
    if not settings.feiertag_active and settings.worker_mode != "sammeln":
        return None
    
    efficiency = min(1.0, idle_workers / 100)
    
    results = {
        "materials": {},
        "farmable_food": {},
        "forageable_food": {},
        "total_food_found": 0.0
    }
    
    for resource_name, base, rmin, rmax in MATERIAL_LOOT:
        resource = db.query(Resource).filter(Resource.name == resource_name).first()
        if not resource:
            continue
        
        amount = (base + random.uniform(rmin, rmax)) * efficiency
        results["materials"][resource_name] = round(amount, 2)
        
        lager_entry = db.query(ProvinceLager).filter(
            ProvinceLager.provinz_id == province_id,
            ProvinceLager.ressource_id == resource.id
        ).first()
        
        if not lager_entry:
            lager_entry = ProvinceLager(
                provinz_id=province_id,
                ressource_id=resource.id,
                menge=0
            )
            db.add(lager_entry)
        
        lager_entry.menge += int(amount)
    
    food_target = idle_workers * random.uniform(2.0, 4.0)
    food_found = 0.0
    
    possible_crops = get_terrain_possible_crops(province.terrain)
    
    for crop_name in possible_crops:
        resource = db.query(Resource).filter(Resource.name == crop_name).first()
        if not resource:
            continue
        
        crop_amount = (0.3 + random.uniform(0.1, 0.6)) * efficiency
        results["farmable_food"][crop_name] = round(crop_amount, 2)
        food_found += crop_amount
        
        lager_entry = db.query(ProvinceLager).filter(
            ProvinceLager.provinz_id == province_id,
            ProvinceLager.ressource_id == resource.id
        ).first()
        
        if not lager_entry:
            lager_entry = ProvinceLager(
                provinz_id=province_id,
                ressource_id=resource.id,
                menge=0
            )
            db.add(lager_entry)
        
        lager_entry.menge += int(crop_amount)
    
    for resource_name, base, rmin, rmax, bonus_terrains in FORAGE_LOOT:
        resource = db.query(Resource).filter(Resource.name == resource_name).first()
        if not resource:
            continue
        
        bonus = 1.5 if province.terrain in bonus_terrains else 1.0
        amount = (base + random.uniform(rmin, rmax)) * efficiency * bonus
        
        results["forageable_food"][resource_name] = round(amount, 2)
        food_found += amount
        
        lager_entry = db.query(ProvinceLager).filter(
            ProvinceLager.provinz_id == province_id,
            ProvinceLager.ressource_id == resource.id
        ).first()
        
        if not lager_entry:
            lager_entry = ProvinceLager(
                provinz_id=province_id,
                ressource_id=resource.id,
                menge=0
            )
            db.add(lager_entry)
        
        lager_entry.menge += int(amount)
    
    if food_found < food_target and not settings.feiertag_active:
        gap = food_target - food_found
        notration_resource = db.query(Resource).filter(Resource.name == "Notrationen").first()
        if notration_resource:
            notration_amount = gap * 0.5
            results["notration_topup"] = round(notration_amount, 2)
            
            lager_entry = db.query(ProvinceLager).filter(
                ProvinceLager.provinz_id == province_id,
                ProvinceLager.ressource_id == notration_resource.id
            ).first()
            
            if not lager_entry:
                lager_entry = ProvinceLager(
                    provinz_id=province_id,
                    ressource_id=notration_resource.id,
                    menge=0
                )
                db.add(lager_entry)
            
            lager_entry.menge += int(notration_amount)
    
    db.commit()
    
    return {
        "success": True,
        "results": results,
        "food_target": round(food_target, 2)
    }

def get_jagd_loot(db: Session, province_id: int):
    province = db.query(Province).filter(Province.id == province_id).first()
    if not province:
        return None
    
    settings = db.query(ProvinceSettings).filter(
        ProvinceSettings.province_id == province_id
    ).first()
    
    if not settings:
        settings = ProvinceSettings(province_id=province_id)
        db.add(settings)
    
    if not settings.feiertag_active and settings.worker_mode != "jagen":
        return None
    
    idle_workers = get_idle_workers(db, province_id)
    efficiency = min(1.0, idle_workers / 100)
    
    loot_results = []
    
    jagd_loot_entries = db.query(JagdLoot).filter(
        JagdLoot.terrain_id == province.terrain
    ).all()
    
    for loot in jagd_loot_entries:
        resource = db.query(Resource).filter(Resource.id == loot.resource_id).first()
        if not resource:
            continue
        
        if loot.is_animal:
            capture_roll = random.random()
            if capture_roll < loot.capture_chance * efficiency:
                amount = 1
                loot_results.append({
                    "resource": resource.name,
                    "amount": amount,
                    "type": "live_animal"
                })
                
                lager_entry = db.query(ProvinceLager).filter(
                    ProvinceLager.provinz_id == province_id,
                    ProvinceLager.ressource_id == resource.id
                ).first()
                
                if not lager_entry:
                    lager_entry = ProvinceLager(
                        provinz_id=province_id,
                        ressource_id=resource.id,
                        menge=0
                    )
                    db.add(lager_entry)
                
                lager_entry.menge += amount
        else:
            amount = (loot.base_amount + random.uniform(loot.random_min, loot.random_max)) * efficiency
            loot_results.append({
                "resource": resource.name,
                "amount": round(amount, 2),
                "type": "material"
            })
            
            lager_entry = db.query(ProvinceLager).filter(
                ProvinceLager.provinz_id == province_id,
                ProvinceLager.ressource_id == resource.id
            ).first()
            
            if not lager_entry:
                lager_entry = ProvinceLager(
                    provinz_id=province_id,
                    ressource_id=resource.id,
                    menge=0
                )
                db.add(lager_entry)
            
            lager_entry.menge += int(amount)
    
    fleisch_resource = db.query(Resource).filter(Resource.name == "Fleisch").first()
    if fleisch_resource:
        fleisch_amount = 1.0 + random.uniform(0.0, 2.5) * efficiency
        loot_results.append({
            "resource": "Fleisch",
            "amount": round(fleisch_amount, 2),
            "type": "material"
        })
        
        lager_entry = db.query(ProvinceLager).filter(
            ProvinceLager.provinz_id == province_id,
            ProvinceLager.ressource_id == fleisch_resource.id
        ).first()
        
        if not lager_entry:
            lager_entry = ProvinceLager(
                provinz_id=province_id,
                ressource_id=fleisch_resource.id,
                menge=0
            )
            db.add(lager_entry)
        
        lager_entry.menge += int(fleisch_amount)
    
    fell_resource = db.query(Resource).filter(Resource.name == "Fell").first()
    if fell_resource:
        fell_amount = 0.5 + random.uniform(0.0, 1.5) * efficiency
        loot_results.append({
            "resource": "Fell",
            "amount": round(fell_amount, 2),
            "type": "material"
        })
        
        lager_entry = db.query(ProvinceLager).filter(
            ProvinceLager.provinz_id == province_id,
            ProvinceLager.ressource_id == fell_resource.id
        ).first()
        
        if not lager_entry:
            lager_entry = ProvinceLager(
                provinz_id=province_id,
                ressource_id=fell_resource.id,
                menge=0
            )
            db.add(lager_entry)
        
        lager_entry.menge += int(fell_amount)
    
    db.commit()
    
    return {
        "success": True,
        "results": loot_results
    }

def get_loot_preview(db: Session, province_id: int):
    province = db.query(Province).filter(Province.id == province_id).first()
    if not province:
        return None
    
    settings = db.query(ProvinceSettings).filter(
        ProvinceSettings.province_id == province_id
    ).first()
    
    if not settings:
        settings = ProvinceSettings(province_id=province_id)
        db.add(settings)
    
    idle_workers = get_idle_workers(db, province_id)
    efficiency = min(1.0, idle_workers / 100)
    
    preview = {
        "province_id": province_id,
        "terrain": province.terrain,
        "idle_workers": idle_workers,
        "worker_mode": settings.worker_mode,
        "feiertag_active": bool(settings.feiertag_active),
        "estimates": {}
    }
    
    if settings.worker_mode == "sammeln":
        materials = {}
        for resource_name, base, rmin, rmax in MATERIAL_LOOT:
            avg = (base + (rmin + rmax) / 2) * efficiency
            materials[resource_name] = round(avg, 2)
        
        possible_crops = get_terrain_possible_crops(province.terrain)
        farmable = {}
        for crop in possible_crops:
            avg = (0.3 + 0.35) * efficiency
            farmable[crop] = round(avg, 2)
        
        forage = {}
        for resource_name, base, rmin, rmax, bonus_terrains in FORAGE_LOOT:
            bonus = 1.5 if province.terrain in bonus_terrains else 1.0
            avg = (base + (rmin + rmax) / 2) * efficiency * bonus
            forage[resource_name] = round(avg, 2)
        
        preview["estimates"] = {
            "materials": materials,
            "farmable_food": farmable,
            "forageable_food": forage
        }
        
    elif settings.worker_mode == "jagen":
        jagd_entries = db.query(JagdLoot).filter(
            JagdLoot.terrain_id == province.terrain
        ).all()
        
        jagd_estimates = {}
        for loot in jagd_entries:
            avg = (loot.base_amount + (loot.random_min + loot.random_max) / 2) * efficiency
            jagd_estimates[db.query(Resource).filter(Resource.id == loot.resource_id).first().name] = round(avg, 2)
        
        preview["estimates"] = {
            "jagd_loot": jagd_estimates,
            "base_fleisch": round(1.0 + 1.25 * efficiency, 2),
            "base_fell": round(0.5 + 0.75 * efficiency, 2)
        }
    
    return preview
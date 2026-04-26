from sqlalchemy.orm import Session
from .models import Province, Player, BuildingInstance, BuildingType, TaxSettings, Resource, ProvinceLager
import json

def has_steueramt(db: Session, province_id: int) -> bool:
    building = db.query(BuildingInstance).join(BuildingType).filter(
        BuildingInstance.provinz_id == province_id,
        BuildingType.name == "Steueramt"
    ).first()
    return building is not None

def has_bank(db: Session, province_id: int) -> bool:
    building = db.query(BuildingInstance).join(BuildingType).filter(
        BuildingInstance.provinz_id == province_id,
        BuildingType.name == "Steueramt"
    ).first()
    if not building:
        return False
    spec = json.loads(building.type.spezial_eigenschaften or "{}")
    return bool(spec.get("bankfunktion", 0))

def get_pkv(db: Session, province_id: int) -> float:
    province = db.query(Province).filter(Province.id == province_id).first()
    if not province or province.population <= 0:
        return 0.0
    population = float(province.population)
    pkv = province.volkskonto / population
    return pkv

def get_tax_settings(db: Session, province_id: int) -> TaxSettings:
    settings = db.query(TaxSettings).filter(
        TaxSettings.province_id == province_id
    ).first()
    if not settings:
        settings = TaxSettings(province_id=province_id)
        db.add(settings)
        db.commit()
    return settings

def update_tax_settings(db: Session, province_id: int, 
                        tax_rate: int = None, lohn_rate: float = None,
                        sold_rate: float = None, rente_rate: float = None,
                        state_transfer_pct: int = None) -> dict:
    province = db.query(Province).filter(Province.id == province_id).first()
    if not province:
        return {"success": False, "error": "Province not found"}
    
    settings = get_tax_settings(db, province_id)
    
    old_tax_rate = settings.tax_rate
    
    if tax_rate is not None:
        settings.tax_rate = max(0, min(100, tax_rate))
    if lohn_rate is not None:
        settings.lohn_rate = max(0, lohn_rate)
    if sold_rate is not None:
        settings.sold_rate = max(0, sold_rate)
    if rente_rate is not None:
        settings.rente_rate = max(0, rente_rate)
    if state_transfer_pct is not None:
        settings.state_transfer_pct = max(0, min(100, state_transfer_pct))
    
    db.commit()
    
    if tax_rate is not None and old_tax_rate != settings.tax_rate:
        apply_tax_moral_impact(db, province_id, old_tax_rate, settings.tax_rate)
    
    return {
        "success": True,
        "tax_rate": settings.tax_rate,
        "lohn_rate": settings.lohn_rate,
        "sold_rate": settings.sold_rate,
        "rente_rate": settings.rente_rate,
        "state_transfer_pct": settings.state_transfer_pct
    }

def apply_tax_moral_impact(db: Session, province_id: int, old_rate: int, new_rate: int):
    province = db.query(Province).filter(Province.id == province_id).first()
    if not province:
        return
    
    delta = new_rate - old_rate
    if delta > 0:
        province.moral -= delta * 1.5
    elif delta < 0:
        province.moral += abs(delta) * 1.0
    
    province.moral = max(0, min(100, province.moral))
    db.commit()

def process_münzerei_production(db: Session, province_id: int):
    province = db.query(Province).filter(Province.id == province_id).first()
    if not province:
        return {"produced": 0, "consumed": {}}
    
    buildings = db.query(BuildingInstance).join(BuildingType).filter(
        BuildingInstance.provinz_id == province_id,
        BuildingType.name == "Münzerei"
    ).all()
    
    if not buildings:
        return {"produced": 0, "consumed": {}}
    
    copper_resource = db.query(Resource).filter(Resource.name == "Kupfer").first()
    if not copper_resource:
        return {"produced": 0, "error": "Kupfer resource not found"}
    
    total_produced = 0
    consumed = {}
    
    for building in buildings:
        spec = json.loads(building.type.spezial_eigenschaften or "{}")
        mips_production = spec.get("mipsproduktion", 1500)
        
        consume_data = json.loads(building.type.rohstoffverbrauch or "[]")
        for cons in consume_data:
            if cons.get("ressource") == "Kupfer":
                copper_needed = cons.get("menge", 0.05)
                
                lager_item = db.query(ProvinceLager).filter(
                    ProvinceLager.provinz_id == province_id,
                    ProvinceLager.ressource_id == copper_resource.id
                ).first()
                
                available = lager_item.menge if lager_item else 0
                
                can_consume = min(available, copper_needed)
                
                if lager_item:
                    lager_item.menge -= can_consume
                
                copper_key = str(copper_resource.id)
                consumed[copper_key] = consumed.get(copper_key, 0) + can_consume
                
                efficiency = can_consume / copper_needed if copper_needed > 0 else 0
                produced = mips_production * efficiency
                
                province.provinzkonto += produced
                total_produced += produced
    
    return {"produced": total_produced, "consumed": consumed}

def process_tax_collection(db: Session, province_id: int):
    if not has_steueramt(db, province_id):
        return {"collected": 0, "warnings": []}
    
    province = db.query(Province).filter(Province.id == province_id).first()
    if not province:
        return {"collected": 0, "warnings": []}
    
    settings = get_tax_settings(db, province_id)
    
    warnings = []
    
    pkv = get_pkv(db, province_id)
    if pkv < 0:
        warnings.append("PKV_NEGATIVE")
        return {"collected": 0, "warnings": warnings}
    
    tax_rate = settings.tax_rate
    if tax_rate <= 0:
        return {"collected": 0, "warnings": []}
    
    tax_amount = province.volkskonto * (tax_rate / 100.0)
    
    bank_bonus = 1.2 if has_bank(db, province_id) else 1.0
    
    collected = tax_amount * bank_bonus
    province.provinzkonto += collected
    province.volkskonto -= tax_amount
    
    return {"collected": collected, "bank_bonus": bank_bonus == 1.2, "warnings": warnings}

def process_wages_and_sold(db: Session, province_id: int):
    if not has_steueramt(db, province_id):
        return {"wages_paid": 0, "sold_paid": 0}
    
    province = db.query(Province).filter(Province.id == province_id).first()
    if not province:
        return {"wages_paid": 0, "sold_paid": 0}
    
    settings = get_tax_settings(db, province_id)
    
    total_workers = sum(b.type.arbeiter for b in province.buildings if b.type and b.type.arbeiter)
    wages = total_workers * settings.lohn_rate
    
    units_count = province.einheiten_count or 0
    sold = units_count * settings.sold_rate
    
    total_paid = wages + sold
    
    if province.provinzkonto < total_paid:
        available = province.provinzkonto
        wages_ratio = wages / total_paid if total_paid > 0 else 0
        
        province.provinzkonto = 0
        province.volkskonto += available * wages_ratio
    else:
        province.provinzkonto -= total_paid
        province.volkskonto += wages + sold
    
    return {"wages_paid": wages, "sold_paid": sold}

def process_state_transfer(db: Session, province_id: int):
    if not has_bank(db, province_id) and not has_steueramt(db, province_id):
        return {"transferred": 0}
    
    province = db.query(Province).filter(Province.id == province_id).first()
    if not province:
        return {"transferred": 0}
    
    settings = get_tax_settings(db, province_id)
    
    if settings.state_transfer_pct <= 0:
        return {"transferred": 0}
    
    player = db.query(Player).filter(Player.id == province.player_id).first()
    if not player:
        return {"transferred": 0}
    
    transfer_amount = province.provinzkonto * (settings.state_transfer_pct / 100.0)
    
    if transfer_amount > 0:
        province.provinzkonto -= transfer_amount
        player.staatskonto += transfer_amount
    
    return {"transferred": transfer_amount}

def process_daily_finance_tick(db: Session, province_id: int):
    results = {
        "province_id": province_id,
        "münzerei_produced": 0,
        "tax_collected": 0,
        "wages_paid": 0,
        "sold_paid": 0,
        "state_transferred": 0,
        "warnings": []
    }
    
    münzerei_result = process_münzerei_production(db, province_id)
    results["münzerei_produced"] = münzerei_result.get("produced", 0)
    results["warnings"].extend(münzerei_result.get("warnings", []))
    
    tax_result = process_tax_collection(db, province_id)
    results["tax_collected"] = tax_result.get("collected", 0)
    results["warnings"].extend(tax_result.get("warnings", []))
    
    wages_result = process_wages_and_sold(db, province_id)
    results["wages_paid"] = wages_result.get("wages_paid", 0)
    results["sold_paid"] = wages_result.get("sold_paid", 0)
    
    transfer_result = process_state_transfer(db, province_id)
    results["state_transferred"] = transfer_result.get("transferred", 0)
    
    db.commit()
    
    return results

def get_finance_info(db: Session, province_id: int) -> dict:
    province = db.query(Province).filter(Province.id == province_id).first()
    if not province:
        return None
    
    player = db.query(Player).filter(Player.id == province.player_id).first()
    
    pkv = get_pkv(db, province_id)
    
    settings = get_tax_settings(db, province_id)
    
    return {
        "province_id": province_id,
        "provinzkonto": province.provinzkonto,
        "volkskonto": province.volkskonto,
        "handelskonto": province.handelskonto,
        "staatskonto": player.staatskonto if player else 0,
        "pkv": pkv,
        "has_steueramt": has_steueramt(db, province_id),
        "has_bank": has_bank(db, province_id),
        "tax_rate": settings.tax_rate,
        "lohn_rate": settings.lohn_rate,
        "sold_rate": settings.sold_rate,
        "rente_rate": settings.rente_rate,
        "state_transfer_pct": settings.state_transfer_pct
    }

def transfer_money(db: Session, province_id: int, amount: float, to_account: str) -> dict:
    if amount <= 0:
        return {"success": False, "error": "Amount must be positive"}
    
    province = db.query(Province).filter(Province.id == province_id).first()
    if not province:
        return {"success": False, "error": "Province not found"}
    
    valid_targets = ["provinzkonto", "volkskonto", "handelskonto", "staatskonto"]
    if to_account not in valid_targets:
        return {"success": False, "error": f"Invalid target: {to_account}. Valid: {valid_targets}"}
    
    if to_account == "staatskonto":
        player = db.query(Player).filter(Player.id == province.player_id).first()
        if not player:
            return {"success": False, "error": "Player not found"}
        
        if province.provinzkonto < amount:
            return {"success": False, "error": "Insufficient funds in Provincialkonto"}
        
        province.provinzkonto -= amount
        player.staatskonto += amount
    elif to_account == "handelskonto":
        if province.provinzkonto < amount:
            return {"success": False, "error": "Insufficient funds in Provincialkonto"}
        
        province.provinzkonto -= amount
        province.handelskonto += amount
    elif to_account == "volkskonto":
        if province.provinzkonto < amount:
            return {"success": False, "error": "Insufficient funds in Provincialkonto"}
        
        province.provinzkonto -= amount
        province.volkskonto += amount
    
    db.commit()
    
    return {
        "success": True,
        "amount": amount,
        "to": to_account
    }
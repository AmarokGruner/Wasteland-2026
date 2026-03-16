from sqlalchemy.orm import Session
from .models import Province, Player, BuildingInstance, BuildingType, Regierungsform
import json

from .regierungsform_logic import (
    get_regierungsform as _get_reg,
    get_kultur_mult as _get_kult,
    get_forschungs_mult as _get_for,
    get_produktivitaet_mult as _get_prod,
    get_provinz_max_without_penalty as _get_prov_max
)


def get_regierungsform(db: Session, player_id: int) -> Regierungsform:
    return _get_reg(db, player_id)


def get_kultur_mult(db: Session, player_id: int) -> float:
    return _get_kult(db, player_id)


def get_forschungs_mult(db: Session, player_id: int) -> float:
    return _get_for(db, player_id)


def get_produktivitaet_mult(db: Session, player_id: int) -> float:
    return _get_prod(db, player_id)


def get_provinz_max_without_penalty(db: Session, player_id: int) -> int:
    return _get_prov_max(db, player_id)

def process_kultur_and_tech_tick(db: Session, province_id: int):
    from .population_logic import calculate_bildung
    
    province = db.query(Province).filter(Province.id == province_id).first()
    if not province:
        return {"kultur": 0, "tech_production": 0}
    
    player = db.query(Player).filter(Player.id == province.player_id).first()
    if not player:
        return {"kultur": 0, "tech_production": 0}
    
    reg = get_regierungsform(db, player.id)
    kultur_mult = reg.kulturverbreitung if reg else 1.0
    forschungs_mult = reg.forschungsfortschritt if reg else 1.0
    
    daily_kultur = province.size_level
    tech_points_base = 0
    
    for building in province.buildings:
        spec = json.loads(building.type.spezial_eigenschaften or "{}")
        
        kultur_delta = spec.get("kulturpunkte", 0)
        if kultur_delta:
            daily_kultur += kultur_delta * building.level
        
        tech_delta = spec.get("techproduktion", 0)
        if tech_delta:
            tech_points_base += tech_delta * building.level
    
    if province.terrain and "Ruine" in province.terrain:
        # Tech points from ruins (manual check for terrain features)
        tech_points_base += 2
    
    daily_kultur *= kultur_mult
    
    bildung = calculate_bildung(db, province_id)
    tech_multiplier = 1 + (bildung / 100.0)
    
    tech_production = int(tech_points_base * tech_multiplier * forschungs_mult)
    
    province.kulturpunkte += int(daily_kultur)
    province.kultureinfluss_total += daily_kultur
    province.tech_production = tech_production
    
    db.commit()
    
    return {
        "kultur": int(daily_kultur),
        "tech_production": tech_production,
        "bildung": bildung
    }

def process_player_tech_level(db: Session, player_id: int):
    from .population_logic import calculate_bildung
    
    player = db.query(Player).filter(Player.id == player_id).first()
    if not player:
        return {"tech_gained": 0}
    
    total_tech = 0
    province_details = []
    
    for province in player.provinces:
        tech_production = province.tech_production or 0
        bildung = calculate_bildung(db, province.id)
        
        reg = get_regierungsform(db, player_id)
        forschungs_mult = reg.forschungsfortschritt if reg else 1.0
        
        tech_gained = int(tech_production * forschungs_mult)
        
        if tech_gained > 0:
            player.tech_level += tech_gained
            total_tech += tech_gained
        
        province_details.append({
            "province_id": province.id,
            "province_name": province.name,
            "tech_production": tech_production,
            "bildung": bildung,
            "tech_gained": tech_gained
        })
    
    db.commit()
    
    return {
        "tech_gained": total_tech,
        "total_tech_level": player.tech_level,
        "provinces": province_details
    }

def process_multi_province_moral_penalty(db: Session, player_id: int):
    player = db.query(Player).filter(Player.id == player_id).first()
    if not player:
        return {"affected_provinces": 0, "total_moral_loss": 0}
    
    reg = get_regierungsform(db, player_id)
    if not reg:
        return {"affected_provinces": 0, "total_moral_loss": 0}
    
    provinz_max = reg.provinzanzahl_bis_malus or 2
    province_count = len(player.provinces)
    
    extra_provinces = max(0, province_count - provinz_max)
    
    malus_per_province = 16
    total_moral_loss_size = extra_provinces * malus_per_province
    
    for province in player.provinces:
        moral_loss = total_moral_loss_size
        
        # Foreign culture check (from 09_kulturpunkte)
        # malus only if fremdkultur_verlust == 1 (Regierungsform)
        if reg.fremdkultur_verlust == 1:
            # Check if there is significant foreign culture influence
            # Simplified: if owner of culture influence is not the player
            if province.kultureinfluss_owner_id and province.kultureinfluss_owner_id != player_id:
                # Deduct extra moral or handle loss
                moral_loss += 10 # Example constant malus for foreign culture
        
        province.moral = max(0, province.moral - moral_loss)
    
    db.commit()
    
    return {
        "affected_provinces": province_count,
        "extra_provinces": extra_provinces,
        "total_moral_loss_base": total_moral_loss_size
    }

def get_kultur_influence_data(db: Session, province_id: int) -> dict:
    province = db.query(Province).filter(Province.id == province_id).first()
    if not province:
        return {}
    
    player = db.query(Player).filter(Player.id == province.player_id).first()
    if not player:
        return {}
    
    reg = get_regierungsform(db, player.id)
    kultur_mult = reg.kultureinfluss if reg else 1.0
    
    daily_kultur = province.size_level
    for building in province.buildings:
        spec = json.loads(building.type.spezial_eigenschaften or "{}")
        daily_kultur += spec.get("kulturpunkte", 0) * building.level
    
    total_kultur = province.kultureinfluss_total or 0
    next_annex_threshold = 100.0
    
    can_annex = total_kultur >= next_annex_threshold
    progress_to_annex = (total_kultur % next_annex_threshold) / next_annex_threshold * 100
    
    return {
        "province_id": province_id,
        "kulturpunkte_daily": int(daily_kultur * kultur_mult),
        "kultureinfluss_total": total_kultur,
        "can_annex_field": can_annex,
        "progress_percent": round(progress_to_annex, 1),
        "next_annex_at": next_annex_threshold
    }

def set_player_regierungsform(db: Session, player_id: int, form_id: int) -> dict:
    from .regierungsform_logic import set_player_regierungsform as _set_form
    return _set_form(db, player_id, form_id)
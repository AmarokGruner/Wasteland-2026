from sqlalchemy.orm import Session
from .models import Player, Province, Regierungsform


ANARCHIE_FORM_ID = 2
TRANSITION_TICKS = 5

def get_regierungsform(db: Session, player_id: int) -> Regierungsform:
    player = db.query(Player).filter(Player.id == player_id).first()
    if not player:
        return None
    
    form_id = player.regierungsform_id
    reg = db.query(Regierungsform).filter(
        Regierungsform.id == form_id
    ).first()
    
    if not reg:
        reg = db.query(Regierungsform).filter(Regierungsform.id == 1).first()
    
    return reg


def is_in_transition(player: Player) -> bool:
    return player.regierungsform_transition_ticks_remaining > 0


def get_current_regierungsform_data(db: Session, player_id: int) -> dict:
    """Returns current form with all modifiers or Anarchie if in transition."""
    player = db.query(Player).filter(Player.id == player_id).first()
    if not player:
        return None
    
    if is_in_transition(player):
        anarchie = db.query(Regierungsform).filter(
            Regierungsform.id == ANARCHIE_FORM_ID
        ).first()
        
        if not anarchie:
            return None
        
        return {
            "is_transition": True,
            "ticks_remaining": player.regierungsform_transition_ticks_remaining,
            "form_id": anarchie.id,
            "name": f"Anarchie (Übergang: {player.regierungsform_transition_ticks_remaining} Ticks)",
            "produktivitaet": 0.9,
            "wachstum": 1.0,
            "sicherheit": 0.5,
            "finanzen": 1.0,
            "forschungsfortschritt": 0.0,
            "kulturverbreitung": 1.0,
            "grundmoral": 30,
            "lebensmittelbedarf": 1.0,
            "verbrauchsgutbedarf": 1.0,
            "streikbereitschaft": 0.5,
            "auswanderbereitschaft": 1.0,
            "milizen": 1.5,
            "fremdkultur_verlust": 0,
            "aufstand": 1,
            "krieg_moeglich": 0,
        }
    
    reg = get_regierungsform(db, player_id)
    if not reg:
        return None
    
    return {
        "is_transition": False,
        "ticks_remaining": 0,
        "form_id": reg.id,
        "name": reg.name,
        "produktivitaet": reg.produktivitaet or 1.0,
        "wachstum": reg.wachstum or 1.0,
        "sicherheit": reg.sicherheit or 1.0,
        "finanzen": reg.finanzen or 1.0,
        "forschungsfortschritt": reg.forschungsfortschritt or 1.0,
        "kulturverbreitung": reg.kulturverbreitung or 1.0,
        "grundmoral": reg.grundmoral or 50,
        "lebensmittelbedarf": reg.lebensmittelbedarf or 1.0,
        "verbrauchsgutbedarf": reg.verbrauchsgutbedarf or 1.0,
        "streikbereitschaft": reg.streikbereitschaft or 0.0,
        "auswanderbereitschaft": reg.auswanderbereitschaft or 0.0,
        "milizen": reg.milizen or 0.0,
        "fremdkultur_verlust": reg.fremdkultur_verlust or 0,
        "aufstand": reg.aufstand or 0,
        "krieg_moeglich": reg.krieg_moeglich or 0,
    }


def get_produktivitaet_mult(db: Session, player_id: int) -> float:
    data = get_current_regierungsform_data(db, player_id)
    if not data:
        return 1.0
    return data["produktivitaet"]


def get_wachstum_mult(db: Session, player_id: int) -> float:
    data = get_current_regierungsform_data(db, player_id)
    if not data:
        return 1.0
    return data["wachstum"]


def get_sicherheit_mult(db: Session, player_id: int) -> float:
    data = get_current_regierungsform_data(db, player_id)
    if not data:
        return 1.0
    return data["sicherheit"]


def get_finanzen_mult(db: Session, player_id: int) -> float:
    data = get_current_regierungsform_data(db, player_id)
    if not data:
        return 1.0
    return data["finanzen"]


def get_forschungs_mult(db: Session, player_id: int) -> float:
    data = get_current_regierungsform_data(db, player_id)
    if not data:
        return 1.0
    return data["forschungsfortschritt"]


def get_kultur_mult(db: Session, player_id: int) -> float:
    data = get_current_regierungsform_data(db, player_id)
    if not data:
        return 1.0
    return data["kulturverbreitung"]


def get_grundmoral(db: Session, player_id: int) -> int:
    data = get_current_regierungsform_data(db, player_id)
    if not data:
        return 50
    return data["grundmoral"]


def get_lebensmittelbedarf_mult(db: Session, player_id: int) -> float:
    data = get_current_regierungsform_data(db, player_id)
    if not data:
        return 1.0
    return data["lebensmittelbedarf"]


def get_verbrauchsgutbedarf_mult(db: Session, player_id: int) -> float:
    data = get_current_regierungsform_data(db, player_id)
    if not data:
        return 1.0
    return data["verbrauchsgutbedarf"]


def get_streikbereitschaft(db: Session, player_id: int) -> float:
    data = get_current_regierungsform_data(db, player_id)
    if not data:
        return 0.0
    return data["streikbereitschaft"]


def get_auswanderbereitschaft(db: Session, player_id: int) -> float:
    data = get_current_regierungsform_data(db, player_id)
    if not data:
        return 0.0
    return data["auswanderbereitschaft"]


def get_milizen_mult(db: Session, player_id: int) -> float:
    data = get_current_regierungsform_data(db, player_id)
    if not data:
        return 0.0
    return data["milizen"]


def get_fremdkultur_verlust(db: Session, player_id: int) -> int:
    data = get_current_regierungsform_data(db, player_id)
    if not data:
        return 0
    return data["fremdkultur_verlust"]


def get_aufstand(db: Session, player_id: int) -> int:
    data = get_current_regierungsform_data(db, player_id)
    if not data:
        return 0
    return data["aufstand"]


def get_krieg_moeglich(db: Session, player_id: int) -> int:
    data = get_current_regierungsform_data(db, player_id)
    if not data:
        return 0
    return data["krieg_moeglich"]


def get_provinz_max_without_penalty(db: Session, player_id: int) -> int:
    reg = get_regierungsform(db, player_id)
    if not reg:
        return 2
    return reg.provinzanzahl_bis_malus or 2


def can_change_regierungsform(db: Session, player_id: int) -> tuple:
    """Check if player can change regierungsform. Returns (can_change, error_message)."""
    player = db.query(Player).filter(Player.id == player_id).first()
    if not player:
        return False, "Player not found"
    
    if is_in_transition(player):
        return False, "Cannot change form during transition"
    
    return True, None


def check_regierungsform_voraussetzungen(db: Session, player_id: int, form_id: int) -> list:
    """Check if player meets all prerequisites for a regierungsform. Returns list of warnings."""
    warnings = []
    
    player = db.query(Player).filter(Player.id == player_id).first()
    if not player:
        return ["Player not found"]
    
    reg = db.query(Regierungsform).filter(Regierungsform.id == form_id).first()
    if not reg:
        return ["Regierungsform not found"]
    
    if player.tech_level < reg.techlevel:
        warnings.append(f"Tech-Level {reg.techlevel} required (current: {player.tech_level})")
    
    if reg.ausbauwert_regierungssitz:
        has_sitz = False
        for province in player.provinces:
            for building in province.buildings:
                if building.type.name == "Regierungssitz" and building.level >= reg.ausbauwert_regierungssitz:
                    has_sitz = True
                    break
            if has_sitz:
                break
        if not has_sitz:
            warnings.append(f"Regierungssitz level {reg.ausbauwert_regierungssitz} required")
    
    return warnings


def set_player_regierungsform(db: Session, player_id: int, form_id: int) -> dict:
    """Set player's regierungsform and start transition to Anarchie."""
    player = db.query(Player).filter(Player.id == player_id).first()
    if not player:
        return {"success": False, "error": "Player not found"}
    
    can_change, error = can_change_regierungsform(db, player_id)
    if not can_change:
        return {"success": False, "error": error}
    
    form = db.query(Regierungsform).filter(Regierungsform.id == form_id).first()
    if not form:
        return {"success": False, "error": "Regierungsform not found"}
    
    warnings = check_regierungsform_voraussetzungen(db, player_id, form_id)
    
    player.regierungsform_transition_ticks_remaining = TRANSITION_TICKS
    
    db.commit()
    
    return {
        "success": True,
        "player_id": player_id,
        "target_form_id": form_id,
        "target_form_name": form.name,
        "transition_ticks": TRANSITION_TICKS,
        "anarchie_warnings": warnings
    }


def process_regierungsform_transition(db: Session, player_id: int):
    """Process daily tick for regierungsform transition (call at midnight)."""
    player = db.query(Player).filter(Player.id == player_id).first()
    if not player:
        return None
    
    if not is_in_transition(player):
        return None
    
    player.regierungsform_transition_ticks_remaining -= 1
    
    transition_complete = False
    target_form_id = None
    target_name = ""
    
    if player.regierungsform_transition_ticks_remaining <= 0:
        transition_complete = True
        target_form_id = player.regierungsform_id
        
        target_reg = db.query(Regierungsform).filter(
            Regierungsform.id == target_form_id
        ).first()
        
        if target_reg:
            target_name = target_reg.name
    
    db.commit()
    
    return {
        "player_id": player_id,
        "transition_complete": transition_complete,
        "ticks_remaining": player.regierungsform_transition_ticks_remaining,
        "target_form_id": target_form_id,
        "target_form_name": target_name
    }


def apply_regierungsform_moral_effects(db: Session, player_id: int) -> dict:
    """Apply moral effects from regierungsform (call for each province)."""
    player = db.query(Player).filter(Player.id == player_id).first()
    if not player:
        return {"moraleffekt": 0}
    
    data = get_current_regierungsform_data(db, player_id)
    if not data:
        return {"moraleffekt": 0}
    
    moral_effect = 0
    
    grundmoral = data["grundmoral"]
    province_moral_base = player.provinces[0].moral if player.provinces else 50
    
    moral_effect = grundmoral - 50
    
    return {
        "moraleffekt": moral_effect,
        "grundmoral": grundmoral
    }


def process_regierungsform_daily(db: Session, player_id: int) -> dict:
    """Process daily tick for regierungsform effects (growth, emigration)."""
    player = db.query(Player).filter(Player.id == player_id).first()
    if not player:
        return {"processed": False}
    
    data = get_current_regierungsform_data(db, player_id)
    if not data:
        return {"processed": False}
    
    results = {
        "player_id": player_id,
        "emigration_total": 0,
    }
    
    auswanderbereitschaft = get_auswanderbereitschaft(db, player_id)
    if auswanderbereitschaft > 0:
        for province in player.provinces:
            if province.moral < 60 and province.population > 0:
                moral_diff = max(0, 60 - province.moral)
                
                emigration_factor = auswanderbereitschaft * (moral_diff / 100.0)
                
                emigrants = int(province.population * emigration_factor)
                emigrants = min(emigrants, province.population - 1)
                
                if emigrants > 0:
                    province.population -= emigrants
                    results["emigration_total"] += emigrants
    
    return results


def get_regierungsform_preview(db: Session, player_id: int, form_id: int) -> dict:
    """Get preview of what modifiers a regierungsform would provide."""
    player = db.query(Player).filter(Player.id == player_id).first()
    if not player:
        return None
    
    current = get_current_regierungsform_data(db, player_id)
    
    new_form = db.query(Regierungsform).filter(
        Regierungsform.id == form_id
    ).first()
    
    if not new_form:
        return None
    
    preview_data = {
        "form_id": form_id,
        "name": new_form.name,
    }
    
    fields_to_compare = [
        "produktivitaet", "wachstum", "sicherheit", "finanzen",
        "forschungsfortschritt", "kulturverbreitung", "grundmoral",
        "lebensmittelbedarf", "verbrauchsgutbedarf", "streikbereitschaft",
        "auswanderbereitschaft", "milizen", "fremdkultur_verlust",
        "aufstand", "krieg_moeglich"
    ]
    
    for field in fields_to_compare:
        if hasattr(new_form, field):
            new_val = getattr(new_form, field) or (1.0 if "mult" not in field and field not in ["grundmoral", "streikbereitschaft", "auswanderbereitschaft", "milizen"] else 0)
        else:
            new_val = None
        
        old_val = current.get(field) if current else 1.0
        
        preview_data[field] = {
            "current": old_val,
            "new": new_val,
            "diff": (new_val or 0) - old_val if (new_val is not None and old_val is not None) else 0
        }
    
    return preview_data


def get_all_regierungsformen(db: Session, player_id: int) -> list:
    """Get all available regierungsformen with eligibility info."""
    player = db.query(Player).filter(Player.id == player_id).first()
    
    all_forms = db.query(Regierungsform).all()
    
    result = []
    for form in all_forms:
        eligible = True
        eligibility_reason = ""
        
        if player.tech_level < form.techlevel:
            eligible = False
            eligibility_reason = f"Tech-Level {form.techlevel} required"
        
        if form.ausbauwert_regierungssitz:
            has_sitz = False
            for province in player.provinces:
                for building in province.buildings:
                    if building.type.name == "Regierungssitz" and building.level >= form.ausbauwert_regierungssitz:
                        has_sitz = True
                        break
                if has_sitz:
                    break
            if not has_sitz:
                eligible = False
                eligibility_reason = f"Regierungssitz level {form.ausbauwert_regierungssitz} required"
        
        result.append({
            "id": form.id,
            "name": form.name,
            "formtyp": form.formtyp or "",
            "techlevel": form.techlevel or 0,
            "eligible": eligible,
            "eligibility_reason": eligibility_reason
        })
    
    return result
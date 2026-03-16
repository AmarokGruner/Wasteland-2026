from sqlalchemy.orm import Session
from app.models import Player, DiplomacyRelation


VALID_STATUSES = ["verbündet", "freund", "neutral", "unerwünscht", "feind"]


def get_effective_relation(db: Session, player_a_id: int, player_b_id: int) -> str:
    rel_a = db.query(DiplomacyRelation).filter(
        DiplomacyRelation.player_id == player_a_id,
        DiplomacyRelation.target_player_id == player_b_id
    ).first()
    
    rel_b = db.query(DiplomacyRelation).filter(
        DiplomacyRelation.player_id == player_b_id,
        DiplomacyRelation.target_player_id == player_a_id
    ).first()
    
    status_a = rel_a.status if rel_a else "neutral"
    status_b = rel_b.status if rel_b else "neutral"
    
    if "feind" in [status_a, status_b]:
        return "feind"
    if "unerwünscht" in [status_a, status_b]:
        return "unerwünscht"
    
    if status_a == "verbündet" and status_b == "verbündet":
        return "verbündet"
    if "freund" in [status_a, status_b]:
        return "freund"
    
    return "neutral"


def can_trade_with(db: Session, player_id: int, target_player_id: int) -> bool:
    relation = get_effective_relation(db, player_id, target_player_id)
    return relation not in ["feind", "unerwünscht"]


def can_see_friends_only_listing(db: Session, player_id: int, target_player_id: int) -> bool:
    relation = get_effective_relation(db, player_id, target_player_id)
    return relation in ["freund", "verbündet"]


def can_see_allied_listing(db: Session, player_id: int, target_player_id: int) -> bool:
    relation = get_effective_relation(db, player_id, target_player_id)
    return relation == "verbündet"


def should_auto_attack(db: Session, player_id: int, target_player_id: int) -> bool:
    relation = get_effective_relation(db, player_id, target_player_id)
    return relation == "feind"


def can_declare_war(db: Session, player_id: int) -> tuple[bool, str]:
    player = db.query(Player).filter(Player.id == player_id).first()
    if not player:
        return False, "Player not found"
    
    reg = player.regierungsform
    if not reg:
        return False, "No regierungsform set"
    
    if reg.krieg_moeglich != 1:
        return False, "GOVERNMENT_NO_WAR"
    
    return True, ""


def set_diplomacy_relation(
    db: Session,
    player_id: int,
    target_player_id: int,
    status: str
) -> dict:
    if player_id == target_player_id:
        return {"success": False, "error": "Cannot set diplomacy to self"}
    
    if status not in VALID_STATUSES:
        return {"success": False, "error": f"Invalid status. Must be one of: {VALID_STATUSES}"}
    
    player = db.query(Player).filter(Player.id == player_id).first()
    target = db.query(Player).filter(Player.id == target_player_id).first()
    
    if not player:
        return {"success": False, "error": "Player not found"}
    if not target:
        return {"success": False, "error": "Target player not found"}
    
    if status == "feind":
        can_war, war_error = can_declare_war(db, player_id)
        if not can_war:
            return {"success": False, "error": war_error}
    
    relation = db.query(DiplomacyRelation).filter(
        DiplomacyRelation.player_id == player_id,
        DiplomacyRelation.target_player_id == target_player_id
    ).first()
    
    if relation:
        relation.status = status
    else:
        relation = DiplomacyRelation(
            player_id=player_id,
            target_player_id=target_player_id,
            status=status
        )
        db.add(relation)
    
    db.commit()
    
    return {"success": True, "relation_id": relation.id if hasattr(relation, 'id') else None}


def get_player_relations(db: Session, player_id: int) -> list:
    relations = db.query(DiplomacyRelation).filter(
        DiplomacyRelation.player_id == player_id
    ).all()
    
    result = []
    for rel in relations:
        effective = get_effective_relation(db, player_id, rel.target_player_id)
        result.append({
            "id": rel.id,
            "player_id": rel.player_id,
            "target_player_id": rel.target_player_id,
            "status": rel.status,
            "effective_relation": effective,
            "updated_at": rel.updated_at.isoformat() if rel.updated_at else None
        })
    
    return result


def get_enemies(db: Session, player_id: int) -> list:
    relations = db.query(DiplomacyRelation).filter(
        DiplomacyRelation.player_id == player_id,
        DiplomacyRelation.status.in_(["feind", "unerwünscht"])
    ).all()
    
    result = []
    for rel in relations:
        target = db.query(Player).filter(Player.id == rel.target_player_id).first()
        result.append({
            "player_id": player_id,
            "target_player_id": rel.target_player_id,
            "target_name": target.name if target else "Unknown",
            "status": rel.status
        })
    
    return result


def is_ally(db: Session, player_id: int, target_player_id: int) -> bool:
    relation = get_effective_relation(db, player_id, target_player_id)
    return relation == "verbündet"


def check_border_crossing(db: Session, moving_player_id: int, target_province_id: int) -> dict:
    """Check if crossing a border triggers a warning or attack"""
    from .models import Province
    target_province = db.query(Province).filter(Province.id == target_province_id).first()
    if not target_province or target_province.player_id == moving_player_id:
        return {"action": "none"}
    
    relation = get_effective_relation(db, moving_player_id, target_province.player_id)
    
    if relation == "feind":
        return {"action": "auto_attack", "message": "Hostile territory! Automatic attack triggered."}
    
    if relation != "verbündet":
        return {"action": "warning", "message": "Crossing foreign borders without alliance!"}
    
    return {"action": "none"}
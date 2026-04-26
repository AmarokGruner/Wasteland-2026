"""
Argentic Function Implementations for Hermes Agent.

These functions are referenced by the block definitions in
`context/blocks/b-arg-function.yaml` and are exposed as entry points
for the Argentic orchestration engine.
"""

from typing import Dict, Any
from sqlalchemy.orm import Session
from fastapi import HTTPException
from app.models import (
    Province,
    Unit,
    Army,
    Player,
    TradeRoute,
    ProvinceSettings,
)
from app.database import get_db
from app.utils import get_current_mips, log_action


# ----------------------------------------------------------------------
# Helper utilities
# ----------------------------------------------------------------------
def _get_province_or_404(province_id: int, db: Session) -> Province:
    """Return province or raise 404."""
    province = db.query(Province).filter(Province.id == province_id).first()
    if not province:
        raise HTTPException(status_code=404, detail=f"Province {province_id} not found")
    return province


def _check_mips(province: Province, required_mips: int) -> None:
    """Validate that the province has enough MIPS for the operation."""
    if province.mips < required_mips:
        raise HTTPException(
            status_code=400,
            detail=f"INSUFFICIENT_MIPS: {province.mips}/{required_mips}",
        )


# ----------------------------------------------------------------------
# Argentic Function: batch_update_units
# ----------------------------------------------------------------------
def batch_update_units(
    province_id: int,
    unit_type: str,
    count: int,
    db: Session,
) -> Dict[str, Any]:
    """
    Bulk‑update of military units across a province.

    This covers training, recruitment, and dismissal of units.
    It returns a structured response that matches the schema defined in
    `b-arg-function.yaml`.

    Args:
        province_id: ID of the target province.
        unit_type:   Type of unit (e.g., "soldier", "cavalry").
        count:       Number of units to process (positive int).

    Returns:
        Dict with keys:
            - unit_id:   Generated unit ID.
            - status:    "success" or "error".
            - message:   Human‑readable description.
    """
    # ------------------------------------------------------------------
    # 1️⃣ Load province and perform basic validation
    # ------------------------------------------------------------------
    province = _get_province_or_404(province_id, db)

    # Determine required MIPS – a simple heuristic:
    #   training: 10 MIPS per unit, recruitment: 15 MIPS per unit
    required_mips = 10 * count if unit_type in ("soldier", "cavalry", "archer") else 15 * count
    _check_mips(province, required_mips)

    # ------------------------------------------------------------------
    # 2️⃣ Determine which backend logic to invoke
    # ------------------------------------------------------------------
    from app.military_logic import train_units, dismiss_units

    try:
        if unit_type in ("soldier", "cavalry", "archer"):
            # Recruit or train new units
            unit = train_units(db, province_id, unit_type, count)
            response = {
                "unit_id": unit.id,
                "status": "success",
                "message": f"Recruited/trained {count} {unit_type}(s).",
            }
        elif unit_type == "dismiss":
            # Dismiss existing units – count represents how many to dismiss
            dismissed = dismiss_units(db, province_id, count)
            response = {
                "unit_id": dismissed.id,
                "status": "success",
                "message": f"Dismissed {count} units.",
            }
        else:
            raise HTTPException(status_code=400, detail=f"Unsupported unit_type: {unit_type}")

    except ValueError as e:
        # Validation errors from train_units / dismiss_units
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        # Unexpected errors – we still want a structured response
        log_action(
            action="batch_update_units_error",
            details={"province_id": province_id, "unit_type": unit_type, "error": str(e)},
        )
        raise HTTPException(status_code=500, detail="Internal server error")

    # ------------------------------------------------------------------
    # 3️⃣ Persist changes and return
    # ------------------------------------------------------------------
    db.commit()
    return response


# ----------------------------------------------------------------------
# Argentic Function: generate_trade_route
# ----------------------------------------------------------------------
def generate_trade_route(
    origin_id: int,
    dest_id: int,
    cargo: str,
    db: Session,
) -> Dict[str, Any]:
    """
    Create a new trade route between two provinces.

    Args:
        origin_id:   ID of the origin province.
        dest_id:     ID of the destination province.
        cargo:       JSON string describing cargo (e.g., '{"food": 100}').

    Returns:
        Dict with keys:
            - route_id:   Generated trade route ID.
            - status:     "success" or "error".
            - message:    Human‑readable description.
    """
    # ------------------------------------------------------------------
    # 1️⃣ Validate provinces exist
    # ------------------------------------------------------------------
    origin = _get_province_or_404(origin_id, db)
    dest = _get_province_or_404(dest_id, db)

    # ------------------------------------------------------------------
    # 2️⃣ Basic sanity checks
    # ------------------------------------------------------------------
    if origin_id == dest_id:
        raise HTTPException(status_code=400, detail="Origin and destination must differ")
    if not origin.sea_access or not dest.sea_access:
        raise HTTPException(status_code=400, detail="Both provinces must have sea access for now")
    # Simple cargo validation – ensure it's a JSON‑compatible string
    try:
        # Attempt to parse as JSON to ensure well‑formedness; we keep the raw string for later use
        import json
        json.loads(cargo)
    except json.JSONDecodeError:
        raise HTTPException(status_code=400, detail="Cargo must be a valid JSON string")

    # ------------------------------------------------------------------
    # 3️⃣ Create TradeRoute instance
    # ------------------------------------------------------------------
    try:
        trade_route = TradeRoute(
            owner_id=origin.player_id,  # assuming owner matches; could be configurable
            origin_province_id=origin_id,
            destination_province_id=dest_id,
            cargo_json=cargo,
            settlers_count=0,
            status="traveling",
        )
        db.add(trade_route)
        db.commit()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create trade route: {e}")

    # ------------------------------------------------------------------
    # 4️⃣ Return structured response
    # ------------------------------------------------------------------
    return {
        "route_id": trade_route.id,
        "status": "success",
        "message": f"Trade route {trade_route.id} created from {origin_id} → {dest_id}",
    }
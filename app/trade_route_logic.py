import json
import math
import datetime
from sqlalchemy.orm import Session
from .models import (
    Province, ProvinceUnit, UnitType, TradeRoute, Resource,
    ProvinceLager, Player, PopulationCohort, GameLog
)


def get_unit_type_by_name(db: Session, name: str):
    return db.query(UnitType).filter(UnitType.name == name).first()


def get_distance(db: Session, origin_id: int, dest_id: int) -> float:
    origin = db.query(Province).filter(Province.id == origin_id).first()
    dest = db.query(Province).filter(Province.id == dest_id).first()
    if not origin or not dest:
        raise ValueError("Invalid province ids for distance calculation")
    dx = origin.world_x - dest.world_x
    dy = origin.world_y - dest.world_y
    return math.sqrt(dx * dx + dy * dy)


def log_game_event(db: Session, province_id: int, event_type: str, message: str, details: dict = None):
    """Helper function to log game events"""
    log_entry = GameLog(
        province_id=province_id,
        event_type=event_type,
        message=message,
        details_json=json.dumps(details or {})
    )
    db.add(log_entry)
    db.commit()


def get_eligible_settlers(db: Session, province_id: int) -> int:
    """Get count of eligible settlers (tick_age 4-5 = 20-25 years old)"""
    cohorts = db.query(PopulationCohort).filter(
        PopulationCohort.province_id == province_id,
        PopulationCohort.tick_age.in_([4, 5])
    ).all()
    return sum(c.count for c in cohorts)


def deduct_eligible_settlers(db: Session, province_id: int, count: int) -> int:
    """Deduct settlers from eligible cohorts, return the tick_age used"""
    remaining = count
    tick_age_used = 4  # Default to youngest eligible

    for tick_age in [4, 5]:  # Prefer younger settlers first
        cohort = db.query(PopulationCohort).filter(
            PopulationCohort.province_id == province_id,
            PopulationCohort.tick_age == tick_age
        ).first()

        if not cohort or cohort.count <= 0:
            continue

        deduct_amount = min(remaining, cohort.count)
        cohort.count -= deduct_amount
        remaining -= deduct_amount
        tick_age_used = tick_age

        if cohort.count == 0:
            db.delete(cohort)

        if remaining == 0:
            break

    return tick_age_used


def create_trade_route(db: Session, province_id: int, destination_id: int, cargo_outbound: dict, settler_count: int, karren_count: int):
    # Validate provinces
    origin = db.query(Province).filter(Province.id == province_id).first()
    dest = db.query(Province).filter(Province.id == destination_id).first()
    if not origin or not dest:
        raise ValueError("Origin or destination province not found")

    # Diplomacy check: Cannot send to enemy province
    if dest.player_id != origin.player_id:
        # TODO: Add diplomacy check here when diplomacy system exists
        pass

    # Validate player ownership
    player = db.query(Player).filter(Player.id == origin.player_id).first()
    if not player:
        raise ValueError("Owner player not found")

    # Validate eligible settlers (tick_age 4-5)
    eligible_count = get_eligible_settlers(db, province_id)
    if eligible_count < settler_count:
        raise ValueError(f"NO_ELIGIBLE_SETTLERS: Need {settler_count}, but only {eligible_count} settlers aged 20-25 available")

    # Validate available karren (Handelskarren)
    karren_type = get_unit_type_by_name(db, "Handelskarren")
    if not karren_type:
        raise ValueError("Handelskarren unit type not defined")
    karren_units = db.query(ProvinceUnit).filter(
        ProvinceUnit.province_id == province_id,
        ProvinceUnit.einheiten_typ_id == karren_type.id
    ).first()
    if not karren_units or karren_units.count < karren_count:
        raise ValueError("Not enough Handelskarren in province")

    # Capacity check: each karren transport_land capacity
    capacity_per_karren = karren_type.transport_land or 100
    total_capacity = capacity_per_karren * karren_count
    total_cargo = sum(cargo_outbound.values())
    if total_cargo > total_capacity:
        raise ValueError(f"Cargo ({total_cargo}) exceeds total transport capacity ({total_capacity})")

    # Validate and deduct cargo from lager
    for res_id, amount in cargo_outbound.items():
        lager_item = db.query(ProvinceLager).filter(
            ProvinceLager.provinz_id == province_id,
            ProvinceLager.ressource_id == int(res_id)
        ).first()
        if not lager_item or lager_item.menge < amount:
            raise ValueError(f"Not enough resource {res_id} in storage")
        lager_item.menge -= amount

    # Deduct eligible settlers from cohorts
    tick_age_used = deduct_eligible_settlers(db, province_id, settler_count)

    # Deduct karren
    karren_units.count -= karren_count
    if karren_units.count == 0:
        db.delete(karren_units)

    # Create route
    route = TradeRoute(
        owner_province_id=province_id,
        destination_province_id=destination_id,
        cargo_outbound_json=json.dumps(cargo_outbound),
        cargo_return_json=json.dumps({}),
        status="loading",
        travel_ticks_remaining=0,
        settler_count=settler_count,
        karren_count=karren_count,
        settler_tick_age=tick_age_used
    )
    db.add(route)
    db.commit()
    db.refresh(route)

    # Log event
    log_game_event(
        db, province_id, "ROUTE_CREATED",
        f"Trade route created to province {destination_id} with {karren_count} karren and {settler_count} settlers",
        {"destination_id": destination_id, "karren_count": karren_count, "settler_count": settler_count, "cargo": cargo_outbound}
    )

    return route


def load_cargo(db: Session, route_id: int, cargo: dict):
    route = db.query(TradeRoute).filter(TradeRoute.id == route_id).first()
    if not route:
        raise ValueError("Trade route not found")
    if route.status != "loading":
        raise ValueError("Can only load cargo while status is loading")
    existing = json.loads(route.cargo_outbound_json)
    # Simple addition, no capacity re-check here (should be done before)
    for res_id, amount in cargo.items():
        existing[str(res_id)] = existing.get(str(res_id), 0) + amount
    route.cargo_outbound_json = json.dumps(existing)
    db.commit()
    return route


def has_pferde_upgrade(db: Session, province_id: int) -> bool:
    """Check if province has Pferde resource available for speed upgrade"""
    # Check if Pferde resource exists in lager
    pferde_res = db.query(Resource).filter(Resource.name == "Pferde").first()
    if not pferde_res:
        return False

    lager_item = db.query(ProvinceLager).filter(
        ProvinceLager.provinz_id == province_id,
        ProvinceLager.ressource_id == pferde_res.id
    ).first()

    return lager_item and lager_item.menge > 0


def depart_route(db: Session, route_id: int):
    route = db.query(TradeRoute).filter(TradeRoute.id == route_id).first()
    if not route:
        raise ValueError("Trade route not found")
    if route.status != "loading":
        raise ValueError("Can only depart from loading state")

    # Calculate travel ticks based on distance and speed
    distance = get_distance(db, route.owner_province_id, route.destination_province_id)

    # Get speed from Handelskarren type
    karren_type = get_unit_type_by_name(db, "Handelskarren")
    speed = karren_type.geschwindigkeit or 0.5

    # Check for Pferde module upgrade (speed bonus)
    if has_pferde_upgrade(db, route.owner_province_id):
        speed *= 2.0  # Double speed with horses

    travel_ticks = max(1, int(distance / speed))
    route.travel_ticks_remaining = travel_ticks
    route.total_travel_ticks = travel_ticks
    route.status = "traveling"
    db.commit()
    return route


def execute_trade_at_destination(db: Session, route_id: int, cargo_return: dict = None):
    """Execute trade when route arrives at destination"""
    route = db.query(TradeRoute).filter(TradeRoute.id == route_id).first()
    if not route:
        raise ValueError("Trade route not found")
    if route.status != "arrived":
        raise ValueError("Can only trade when status is 'arrived'")

    dest_province = db.query(Province).filter(Province.id == route.destination_province_id).first()

    # Deposit outbound cargo to destination lager
    outbound_cargo = json.loads(route.cargo_outbound_json)
    for res_id_str, amount in outbound_cargo.items():
        res_id = int(res_id_str)
        lager_item = db.query(ProvinceLager).filter(
            ProvinceLager.provinz_id == route.destination_province_id,
            ProvinceLager.ressource_id == res_id
        ).first()
        if not lager_item:
            lager_item = ProvinceLager(
                provinz_id=route.destination_province_id,
                ressource_id=res_id,
                menge=0
            )
            db.add(lager_item)
        lager_item.menge += int(amount)

    # Load return cargo if provided
    if cargo_return:
        # Validate cargo availability
        for res_id, amount in cargo_return.items():
            lager_item = db.query(ProvinceLager).filter(
                ProvinceLager.provinz_id == route.destination_province_id,
                ProvinceLager.ressource_id == int(res_id)
            ).first()
            if not lager_item or lager_item.menge < amount:
                raise ValueError(f"Not enough resource {res_id} in destination storage")

        # Deduct cargo from destination lager
        for res_id, amount in cargo_return.items():
            lager_item = db.query(ProvinceLager).filter(
                ProvinceLager.provinz_id == route.destination_province_id,
                ProvinceLager.ressource_id == int(res_id)
            ).first()
            lager_item.menge -= amount

        route.cargo_return_json = json.dumps(cargo_return)

    # Calculate return trip
    distance = get_distance(db, route.destination_province_id, route.owner_province_id)
    karren_type = get_unit_type_by_name(db, "Handelskarren")
    speed = karren_type.geschwindigkeit or 0.5

    # Check for Pferde module upgrade (speed bonus)
    if has_pferde_upgrade(db, route.owner_province_id):
        speed *= 2.0  # Double speed with horses

    travel_ticks = max(1, int(distance / speed))
    route.travel_ticks_remaining = travel_ticks
    route.status = "returning"

    db.commit()

    # Log event
    log_game_event(
        db, route.destination_province_id, "ROUTE_TRADED",
        f"Trade route from province {route.owner_province_id} completed trade and is returning",
        {"origin_id": route.owner_province_id, "cargo_delivered": outbound_cargo, "cargo_return": cargo_return or {}}
    )

    return route


def process_trade_routes(db: Session):
    """Called every tick to process all active trade routes"""
    routes = db.query(TradeRoute).filter(TradeRoute.status.in_(["traveling", "returning"])).all()

    for route in routes:
        # Decrement travel ticks
        if route.travel_ticks_remaining > 0:
            route.travel_ticks_remaining -= 1

        # Arrival handling
        if route.travel_ticks_remaining <= 0:
            if route.status == "traveling":
                # Arrived at destination
                route.status = "arrived"

                # Log event
                log_game_event(
                    db, route.destination_province_id, "ROUTE_ARRIVED",
                    f"Trade route from province {route.owner_province_id} has arrived",
                    {"origin_id": route.owner_province_id, "route_id": route.id}
                )

            elif route.status == "returning":
                # Arrived back home
                return_cargo = json.loads(route.cargo_return_json)

                # Deposit return cargo to origin lager
                for res_id_str, amount in return_cargo.items():
                    res_id = int(res_id_str)
                    lager_item = db.query(ProvinceLager).filter(
                        ProvinceLager.provinz_id == route.owner_province_id,
                        ProvinceLager.ressource_id == res_id
                    ).first()
                    if not lager_item:
                        lager_item = ProvinceLager(
                            provinz_id=route.owner_province_id,
                            ressource_id=res_id,
                            menge=0
                        )
                        db.add(lager_item)
                    lager_item.menge += int(amount)

                # Return settlers to population cohort (preserve tick_age)
                cohort = db.query(PopulationCohort).filter(
                    PopulationCohort.province_id == route.owner_province_id,
                    PopulationCohort.tick_age == route.settler_tick_age
                ).first()
                if not cohort:
                    cohort = PopulationCohort(
                        province_id=route.owner_province_id,
                        tick_age=route.settler_tick_age,
                        count=route.settler_count
                    )
                    db.add(cohort)
                else:
                    cohort.count += route.settler_count

                # Return karren to province units
                karren_type = get_unit_type_by_name(db, "Handelskarren")
                karren_units = db.query(ProvinceUnit).filter(
                    ProvinceUnit.province_id == route.owner_province_id,
                    ProvinceUnit.einheiten_typ_id == karren_type.id
                ).first()
                if not karren_units:
                    karren_units = ProvinceUnit(
                        province_id=route.owner_province_id,
                        einheiten_typ_id=karren_type.id,
                        count=route.karren_count,
                        status="idle"
                    )
                    db.add(karren_units)
                else:
                    karren_units.count += route.karren_count

                # Mark route as completed
                route.status = "home"

                # Log event
                cargo_summary = ", ".join([f"{amt}x res_{res_id}" for res_id, amt in return_cargo.items()])
                log_game_event(
                    db, route.owner_province_id, "ROUTE_RETURNED",
                    f"Trade route returned with cargo: {cargo_summary or 'empty'}",
                    {"cargo": return_cargo, "settler_count": route.settler_count, "karren_count": route.karren_count}
                )

    db.commit()

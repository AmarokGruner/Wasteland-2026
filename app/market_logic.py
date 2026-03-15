from sqlalchemy.orm import Session
from .models import Province, MarketStand, Resource, ProvinceLager, ProvinceSettings
import json

def get_market_demand(db: Session, province_id: int):
    """
    Calculates the 24h demand for each resource category based on population.
    Standard consumption: 1 unit per 10 population per 24h for 'Nahrung' and 'Getränk'.
    """
    province = db.query(Province).filter(Province.id == province_id).first()
    if not province:
        return {}

    # demand_per_category = population * consumption_rate[category]
    # According to round_logic.py: population / 10.0 * 1.0
    demand_per_pop = 1.0 / 10.0
    total_demand = province.population * demand_per_pop

    return {
        "Nahrung": total_demand,
        "Getränk": total_demand
    }

def process_market_tick(db: Session, province_id: int):
    """
    Processes the daily market logic:
    1. Calculate demand.
    2. Split demand among active market stands.
    3. Market buys supply for 5 days from Lager (Market Buy).
    4. Adjust Staatswert if supply is abundant (Staatswert Floor).
    """
    province = db.query(Province).filter(Province.id == province_id).first()
    if not province or province.population <= 0:
        return

    # 1. DEMAND CALCULATION
    demand_per_category = get_market_demand(db, province_id)

    # 2. STAND SPLIT & 3. MARKET BUY
    # Get all active stands for this province
    stands = db.query(MarketStand).filter(MarketStand.province_id == province_id).all()
    
    # Group stands by category
    stands_by_category = {}
    for stand in stands:
        res = stand.resource
        if res.typ not in stands_by_category:
            stands_by_category[res.typ] = []
        stands_by_category[res.typ].append(stand)

    total_purchased_value = 0.0

    for category, cat_demand in demand_per_category.items():
        cat_stands = stands_by_category.get(category, [])
        if not cat_stands:
            continue
        
        total_stands_count = len(cat_stands)
        # per_resource_sold = demand * (stands[resource] / total_stands)
        demand_per_stand = cat_demand / total_stands_count

        for stand in cat_stands:
            if not stand.auto_buy:
                continue
            
            res = stand.resource
            # MARKET BUY (pre-purchase):
            # market_stock[resource] += min(demand*5, lager[resource]) 
            # (Note: We don't have a market_stock in DB yet, but the logic says it's sold to population from there)
            # The purchase happens from Lager -> "Market"
            
            lager_item = db.query(ProvinceLager).filter(
                ProvinceLager.provinz_id == province_id,
                ProvinceLager.ressource_id == res.id
            ).first()
            
            if not lager_item or lager_item.menge <= 0:
                continue
            
            # Buy 5-day supply upfront
            buy_amount = min(demand_per_stand * 5, lager_item.menge)
            
            if buy_amount > 0:
                # staatswert * 1.5
                price_per_unit = res.wert * 1.5
                total_price = buy_amount * price_per_unit
                
                # Update Lager
                lager_item.menge -= buy_amount
                
                # Update Accounts
                # provinzkonto += purchased * staatswert * 1.5
                # volkskonto -= purchased * staatswert * 1.5
                province.provinzkonto += total_price
                province.volkskonto -= total_price
                
                total_purchased_value += total_price

    # 4. STAATSWERT FLOOR (Currently not globally implemented, 
    # but we can adjust the resource 'wert' if we want it to be global or just for this calc.
    # The doc says: "if supply_ratio >= 1.0: staatswert = base_value * 0.5 (minimum)"
    # This usually implies a global price calculation based on total supply/demand.
    # For now we keep it as a placeholder or implement it locally if needed.

    db.commit()
    return {"total_purchased_value": total_purchased_value}

def get_market_preview(db: Session, province_id: int):
    """
    Returns data for the market preview endpoint.
    """
    demand = get_market_demand(db, province_id)
    stands = db.query(MarketStand).filter(MarketStand.province_id == province_id).all()
    
    current_stands = []
    for s in stands:
        current_stands.append({
            "resource_id": s.resource_id,
            "resource_name": s.resource.name,
            "category": s.resource.typ,
            "auto_buy": bool(s.auto_buy)
        })
        
    return {
        "demand": demand,
        "current_stands": current_stands,
        "marktpunkte_total": db.query(Province).filter(Province.id == province_id).first().marktpunkte
    }

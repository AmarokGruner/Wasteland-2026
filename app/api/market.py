from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from app.models import get_db, Province, MarketStand, Resource, KontorPrice, TradeRoute, Player
from app.market_logic import get_market_preview, process_market_tick

router = APIRouter(prefix="/province", tags=["market"])

class MarketStandCreate(BaseModel):
    resource_id: int
    auto_buy: bool = True

class KontorPriceUpdate(BaseModel):
    resource_id: int
    mode: str  # "buy" or "sell"
    price: float
    friends_only: bool = False
    verbündete_only: bool = False


class KontorPriceResponse(BaseModel):
    id: int
    resource_id: int
    resource_name: str
    mode: str
    price: float
    friends_only: bool
    verbündete_only: bool


class KontorTradeTransaction(BaseModel):
    resource_id: int
    mode: str  # "buy" or "sell"
    amount: float


class KontorTradeRequest(BaseModel):
    route_id: int
    transactions: list[KontorTradeTransaction]

class TradeRouteCreate(BaseModel):
    destination_province_id: int
    cargo: dict # {resource_id: amount}
    settlers: int = 0

@router.get("/{province_id}/market/stands")
def get_market_stands(province_id: int, db: Session = Depends(get_db)):
    stands = db.query(MarketStand).filter(MarketStand.province_id == province_id).all()
    province = db.query(Province).filter(Province.id == province_id).first()
    if not province:
        raise HTTPException(status_code=404, detail="Province not found")
    
    return {
        "marktpunkte_total": province.marktpunkte,
        "stands_used": len(stands),
        "stands": [
            {
                "id": s.id,
                "resource_id": s.resource_id,
                "resource_name": s.resource.name,
                "category": s.resource.typ,
                "auto_buy": bool(s.auto_buy)
            } for s in stands
        ]
    }

@router.post("/{province_id}/market/stands")
def create_market_stand(province_id: int, request: MarketStandCreate, db: Session = Depends(get_db)):
    province = db.query(Province).filter(Province.id == province_id).first()
    if not province:
        raise HTTPException(status_code=404, detail="Province not found")
    
    # Check marktpunkte limit
    existing_stands_count = db.query(MarketStand).filter(MarketStand.province_id == province_id).count()
    if existing_stands_count >= province.marktpunkte:
        raise HTTPException(status_code=400, detail="Not enough marktpunkte")
    
    # Check resource
    resource = db.query(Resource).filter(Resource.id == request.resource_id).first()
    if not resource:
        raise HTTPException(status_code=404, detail="Resource not found")
    
    # Check if stand for this resource already exists
    existing_stand = db.query(MarketStand).filter(
        MarketStand.province_id == province_id,
        MarketStand.resource_id == request.resource_id
    ).first()
    if existing_stand:
        raise HTTPException(status_code=400, detail="Market stand for this resource already exists")

    new_stand = MarketStand(
        province_id=province_id,
        resource_id=request.resource_id,
        auto_buy=1 if request.auto_buy else 0
    )
    db.add(new_stand)
    db.commit()
    return {"success": True, "stand_id": new_stand.id}

@router.delete("/{province_id}/market/stands/{resource_id}")
def delete_market_stand(province_id: int, resource_id: int, db: Session = Depends(get_db)):
    stand = db.query(MarketStand).filter(
        MarketStand.province_id == province_id,
        MarketStand.resource_id == resource_id
    ).first()
    if not stand:
        raise HTTPException(status_code=404, detail="Market stand not found")
    
    # Dissolve logic: 160% buyback (optional, if we want to give something back)
    # The doc says "dissolve (160% buyback)" - maybe referring to some cost? 
    # Usually building costs something. Stände might be free but limited by points.
    
    db.delete(stand)
    db.commit()
    return {"success": True}

@router.get("/{province_id}/market/preview")
def get_market_preview_endpoint(province_id: int, db: Session = Depends(get_db)):
    return get_market_preview(db, province_id)

@router.get("/{province_id}/kontor/prices")
def get_kontor_prices(province_id: int, visitor_player_id: int = None, db: Session = Depends(get_db)):
    province = db.query(Province).filter(Province.id == province_id).first()
    if not province:
        raise HTTPException(status_code=404, detail="Province not found")
    
    prices = db.query(KontorPrice).filter(
        KontorPrice.province_id == province_id,
        KontorPrice.active == 1
    ).all()
    
    visitor = None
    if visitor_player_id:
        visitor = db.query(Player).filter(Player.id == visitor_player_id).first()
    
    result = []
    for p in prices:
        visible = True
        
        # Price visibility logic
        if visitor and p.friends_only == 1:
            # Check if visitor is friend (simplified - would need player.freunde)
            visible = False
        if visitor and p.verbündete_only == 1:
            # Check if visitor is verbündeter (simplified)
            visible = False
        
        result.append({
            "id": p.id,
            "resource_id": p.resource_id,
            "resource_name": p.resource.name if p.resource else "Unknown",
            "mode": p.mode,
            "price": p.price,
            "friends_only": bool(p.friends_only),
            "verbündete_only": bool(p.verbündete_only),
            "visible": visible
        })
    
    return {"prices": result}


@router.post("/{province_id}/kontor/prices")
def set_kontor_prices(province_id: int, request: KontorPriceUpdate, db: Session = Depends(get_db)):
    province = db.query(Province).filter(Province.id == province_id).first()
    if not province:
        raise HTTPException(status_code=404, detail="Province not found")
    
    # Validate mode
    if request.mode not in ("buy", "sell"):
        raise HTTPException(status_code=400, detail="mode must be 'buy' or 'sell'")
    
    # Check if price entry already exists for this mode/resource
    price_entry = db.query(KontorPrice).filter(
        KontorPrice.province_id == province_id,
        KontorPrice.resource_id == request.resource_id,
        KontorPrice.mode == request.mode
    ).first()
    
    if price_entry:
        price_entry.price = request.price
        price_entry.friends_only = 1 if request.friends_only else 0
        price_entry.verbündete_only = 1 if request.verbündete_only else 0
    else:
        price_entry = KontorPrice(
            province_id=province_id,
            resource_id=request.resource_id,
            mode=request.mode,
            price=request.price,
            friends_only=1 if request.friends_only else 0,
            verbündete_only=1 if request.verbündete_only else 0
        )
        db.add(price_entry)
    
    db.commit()
    return {"success": True, "price_id": price_entry.id}


@router.delete("/{province_id}/kontor/prices/{price_id}")
def delete_kontor_price(province_id: int, price_id: int, db: Session = Depends(get_db)):
    price_entry = db.query(KontorPrice).filter(
        KontorPrice.id == price_id,
        KontorPrice.province_id == province_id
    ).first()
    
    if not price_entry:
        raise HTTPException(status_code=404, detail="Kontor price entry not found")
    
    # Soft delete - just set inactive
    price_entry.active = 0
    db.commit()
    
    return {"success": True}

@router.post("/{province_id}/trade-route/create")
def create_trade_route(province_id: int, request: TradeRouteCreate, db: Session = Depends(get_db)):
    origin = db.query(Province).filter(Province.id == province_id).first()
    if not origin:
        raise HTTPException(status_code=404, detail="Origin province not found")
    
    destination = db.query(Province).filter(Province.id == request.destination_province_id).first()
    if not destination:
        raise HTTPException(status_code=404, detail="Destination province not found")
    
    # Check settlers requirement (aged 20-25) - simplified for now
    # population_cohorts could be used if implemented
    if request.settlers > 0:
        if origin.population < request.settlers:
            raise HTTPException(status_code=400, detail="Not enough population for settlers")
        origin.population -= request.settlers

    new_route = TradeRoute(
        owner_id=origin.player_id,
        origin_province_id=province_id,
        destination_province_id=request.destination_province_id,
        cargo_json=json.dumps(request.cargo),
        settlers_count=request.settlers,
        status="traveling"
    )
    db.add(new_route)
    db.commit()
    return {"success": True, "trade_route_id": new_route.id}

@router.get("/{province_id}/kontor/balance")
def get_kontor_balance(province_id: int, db: Session = Depends(get_db)):
    province = db.query(Province).filter(Province.id == province_id).first()
    if not province:
        raise HTTPException(status_code=404, detail="Province not found")
    
    return {
        "province_id": province_id,
        "handelskonto": province.handelskonto
    }


@router.post("/{province_id}/kontor/trade")
def execute_kontor_trade(province_id: int, request: KontorTradeRequest, db: Session = Depends(get_db)):
    province = db.query(Province).filter(Province.id == province_id).first()
    if not province:
        raise HTTPException(status_code=404, detail="Province not found")
    
    from app.models import BuildingInstance, BuildingType
    kontor = db.query(BuildingInstance).join(BuildingType).filter(
        BuildingInstance.provinz_id == province_id,
        BuildingType.name.like("%Kontor%")
    ).first()
    
    if not kontor:
        raise HTTPException(status_code=400, detail="KONTOR_REQUIRED: Province needs a Kontor to trade")
    
    from app.models import TradeRoute, ProvinceLager
    route = db.query(TradeRoute).filter(TradeRoute.id == request.route_id).first()
    if not route:
        raise HTTPException(status_code=404, detail="Trade route not found")
    
    # Load cargo from route
    import json as json_module
    try:
        cargo = json_module.loads(route.cargo_json) if route.cargo_json else {}
    except:
        cargo = {}
    
    results = []
    
    for tx in request.transactions:
        resource_id = tx.resource_id
        mode = tx.mode  # "buy" or "sell"
        amount = tx.amount
        
        if amount <= 0:
            continue
        
        # Get the price entry
        price_entry = db.query(KontorPrice).filter(
            KontorPrice.province_id == province_id,
            KontorPrice.resource_id == resource_id,
            KontorPrice.mode == mode,
            KontorPrice.active == 1
        ).first()
        
        if not price_entry:
            results.append({
                "resource_id": resource_id,
                "status": "PRICE_NOT_FOUND",
                "message": f"No {mode} price for this resource"
            })
            continue
        
        if mode == "sell":
            # Province sells to visitor (visitor buys from province)
            # Check if province has enough stock
            lager_entry = db.query(ProvinceLager).filter(
                ProvinceLager.provinz_id == province_id,
                ProvinceLager.ressource_id == resource_id
            ).first()
            
            if not lager_entry or lager_entry.menge < amount:
                results.append({
                    "resource_id": resource_id,
                    "status": "INSUFFICIENT_STOCK",
                    "message": "Not enough resources in storage"
                })
                continue
            
            # Execute: decrease province lager, increase visitor cargo, add to handelskonto
            total_cost = amount * price_entry.price
            
            lager_entry.menge -= amount
            province.handelskonto += total_cost
            
            cargo[str(resource_id)] = cargo.get(str(resource_id), 0) + amount
            results.append({
                "resource_id": resource_id,
                "status": "SUCCESS",
                "amount": amount,
                "price": price_entry.price,
                "total": total_cost
            })
            
        elif mode == "buy":
            # Province buys from visitor (visitor sells to province)
            total_cost = amount * price_entry.price
            
            if province.handelskonto < total_cost:
                results.append({
                    "resource_id": resource_id,
                    "status": "INSUFFICIENT_HANDELSKONTO",
                    "message": "Not enough funds in Handelskonto"
                })
                continue
            
            # Execute: decrease handelskonto, increase province lager, decrease visitor cargo
            available_in_cargo = cargo.get(str(resource_id), 0)
            if available_in_cargo < amount:
                results.append({
                    "resource_id": resource_id,
                    "status": "INSUFFICIENT_CARGO",
                    "message": "Not enough resources in visitor cargo"
                })
                continue
            
            province.handelskonto -= total_cost
            
            if lager_entry := db.query(ProvinceLager).filter(
                ProvinceLager.provinz_id == province_id,
                ProvinceLager.ressource_id == resource_id
            ).first():
                lager_entry.menge += amount
            else:
                new_lager = ProvinceLager(
                    provinz_id=province_id,
                    ressource_id=resource_id,
                    menge=amount
                )
                db.add(new_lager)
            
            cargo[str(resource_id)] = available_in_cargo - amount
            results.append({
                "resource_id": resource_id,
                "status": "SUCCESS",
                "amount": amount,
                "price": price_entry.price,
                "total": total_cost
            })
    
    # Update route cargo
    route.cargo_json = json_module.dumps(cargo)
    db.commit()
    
    return {
        "province_id": province_id,
        "route_id": route_id,
        "handelskonto_after": province.handelskonto,
        "transactions": results
    }


import json

from sqlalchemy.orm import Session
import math
from app.models import Province, ProvinceAnimal, AnimalTemplate, ProvinceLager, Resource


def process_wild_animal_feeding(db: Session, province_id: int):
    """Process feeding of wild animals and apply terrain yield malus if starving."""
    province = db.query(Province).filter(Province.id == province_id).first()
    if not province:
        return None
    
    wild_animals = db.query(ProvinceAnimal).filter(
        ProvinceAnimal.province_id == province_id,
        ProvinceAnimal.is_wild == 1
    ).all()
    
    terrain_malus = 0.0
    for animal in wild_animals:
        template = db.query(AnimalTemplate).filter(
            AnimalTemplate.resource_id == animal.animal_resource_id
        ).first()
        if not template or not template.is_pflanzenfresser:
            continue
        
        food_needed = animal.count * template.feed_amount_per_24h
        # Find feed resource in lager
        feed_lager = db.query(ProvinceLager).filter(
            ProvinceLager.provinz_id == province_id,
            ProvinceLager.ressource_id == template.feed_resource_id
        ).first()
        available = feed_lager.menge if feed_lager else 0
        
        if available >= food_needed:
            # consume feed
            if feed_lager:
                feed_lager.menge -= int(food_needed)
        else:
            # starving -> eat fields, apply malus
            starving_ratio = (food_needed - available) / food_needed
            terrain_malus -= starving_ratio * 0.1  # up to -10% per tick
            if feed_lager:
                feed_lager.menge = 0
    
    # Apply terrain malus (capped at -50%)
    province.terrain_yield_malus = max(-0.5, terrain_malus)
    db.commit()
    return terrain_malus


def process_breeding(db: Session, province_id: int):
    """Process breeding in Tierzucht buildings."""
    province = db.query(Province).filter(Province.id == province_id).first()
    if not province:
        return None
    
    # Find breeding buildings (e.g., Hühnerfarm, Nuggretszucht). Assuming they have a special tag in BuildingType.spezial_eigenschaften
    breeding_buildings = [b for b in province.buildings if b.type.spezial_eigenschaften and "tierzucht" in b.type.spezial_eigenschaften]
    
    for building in breeding_buildings:
        # Get animal template from building (assume building.type.spezial_eigenschaften contains animal_resource_id)
        # Example: {"tierzucht": {"animal_resource_id": 42}}
        import json
        special = json.loads(building.type.spezial_eigenschaften)
        animal_info = special.get("tierzucht", {})
        animal_res_id = animal_info.get("animal_resource_id")
        if not animal_res_id:
            continue
        
        template = db.query(AnimalTemplate).filter(AnimalTemplate.resource_id == animal_res_id).first()
        if not template:
            continue
        
        # Get current stock of starter animals
        starter_lager = db.query(ProvinceLager).filter(
            ProvinceLager.provinz_id == province_id,
            ProvinceLager.ressource_id == animal_res_id
        ).first()
        starter_count = starter_lager.menge if starter_lager else 0
        
        # Check feed availability
        feed_lager = db.query(ProvinceLager).filter(
            ProvinceLager.provinz_id == province_id,
            ProvinceLager.ressource_id == template.feed_resource_id
        ).first()
        feed_available = feed_lager.menge if feed_lager else 0
        
        # Minimum stock threshold (let's assume at least 1 starter animal & enough feed for 1 animal)
        if starter_count < 1 or feed_available < template.feed_amount_per_24h:
            continue
        
        # Consume feed for the whole herd (simplified: feed per animal * count)
        total_feed_needed = starter_count * template.feed_amount_per_24h
        if feed_available < total_feed_needed:
            # Not enough feed for full herd, feed what we can
            possible_animals = math.floor(feed_available / template.feed_amount_per_24h)
            feed_to_consume = possible_animals * template.feed_amount_per_24h
        else:
            possible_animals = starter_count
            feed_to_consume = total_feed_needed
        
        if feed_lager:
            feed_lager.menge -= int(feed_to_consume)
        
        # Breed new animals
        new_animals = math.floor(possible_animals * template.breed_rate)
        if new_animals > 0:
            # Add to output resource (e.g., Eier, Fleisch, Fell)
            if template.breed_output_resource_id:
                out_lager = db.query(ProvinceLager).filter(
                    ProvinceLager.provinz_id == province_id,
                    ProvinceLager.ressource_id == template.breed_output_resource_id
                ).first()
                if not out_lager:
                    out_lager = ProvinceLager(provinz_id=province_id, ressource_id=template.breed_output_resource_id, menge=0)
                    db.add(out_lager)
                out_lager.menge += new_animals
        
        # Update starter animal stock (herd grows slowly by adding a fraction of new births)
        # Let's assume the herd size grows by half of the new animals (simplified)
        herd_growth = math.floor(new_animals / 2)
        if starter_lager:
            starter_lager.menge += herd_growth
        else:
            starter_lager = ProvinceLager(provinz_id=province_id, ressource_id=animal_res_id, menge=herd_growth)
            db.add(starter_lager)
    
    db.commit()
    return True

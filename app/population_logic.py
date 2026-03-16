from sqlalchemy.orm import Session
from .models import Province, PopulationCohort, BuildingInstance, BuildingType, TaxSettings
import json

def get_age_group(tick_age: int) -> str:
    if tick_age < 3:
        return "kind"
    elif tick_age < 13:
        return "arbeiter"
    else:
        return "rentner"

def get_death_rate(tick_age: int) -> float:
    if tick_age == 13:
        return 0.05
    elif tick_age == 14:
        return 0.15
    elif tick_age >= 15:
        return 1.0
    return 0.0

def initialize_population_cohorts(db: Session, province_id: int):
    existing = db.query(PopulationCohort).filter(
        PopulationCohort.province_id == province_id
    ).all()
    
    if existing:
        return
    
    province = db.query(Province).filter(Province.id == province_id).first()
    if not province:
        return
    
    initial_population = max(1, province.population)
    
    children_count = int(initial_population * 0.3)
    workers_count = int(initial_population * 0.5)
    retirees_count = initial_population - children_count - workers_count
    
    child_cohort = PopulationCohort(
        province_id=province_id,
        tick_age=0,
        age_group="kind",
        count=children_count
    )
    
    worker_cohort = PopulationCohort(
        province_id=province_id,
        tick_age=3,
        age_group="arbeiter",
        count=workers_count
    )
    
    retiree_cohort = PopulationCohort(
        province_id=province_id,
        tick_age=13,
        age_group="rentner",
        count=retirees_count
    )
    
    db.add(child_cohort)
    db.add(worker_cohort)
    db.add(retiree_cohort)
    db.commit()

def process_population_tick(db: Session, province_id: int):
    initialize_population_cohorts(db, province_id)
    
    process_aging(db, province_id)
    process_deaths(db, province_id)
    process_births(db, province_id)
    
    update_province_population_stats(db, province_id)

def process_aging(db: Session, province_id: int):
    cohorts = db.query(PopulationCohort).filter(
        PopulationCohort.province_id == province_id
    ).all()
    
    for cohort in cohorts:
        old_tick_age = cohort.tick_age
        
        if old_tick_age == 3 and cohort.age_group == "kind":
            cohort.age_group = "arbeiter"
        elif old_tick_age == 13 and cohort.age_group == "arbeiter":
            cohort.age_group = "rentner"
    
    db.commit()

def process_deaths(db: Session, province_id: int):
    cohorts = db.query(PopulationCohort).filter(
        PopulationCohort.province_id == province_id
    ).all()
    
    for cohort in cohorts:
        death_rate = get_death_rate(cohort.tick_age)
        
        if death_rate > 0 and cohort.count > 0:
            deaths = int(cohort.count * death_rate)
            cohort.count -= deaths
            
            if cohort.count <= 0:
                db.delete(cohort)
    
    db.commit()

def process_births(db: Session, province_id: int):
    province = db.query(Province).filter(Province.id == province_id).first()
    if not province:
        return
    
    player = None
    from .models import Player
    player = db.query(Player).filter(Player.id == province.player_id).first()
    
    wachstum = 1.0
    if player:
        wachstum = getattr(player, 'tech_level', 0) / 10.0 + 1.0
    
    bildung = calculate_bildung(db, province_id)
    
    birth_rate = wachstum * (1 - bildung / 200) * 0.02
    
    workers_count = get_cohort_count_by_age_group(db, province_id, "arbeiter")
    
    new_children = int(workers_count * birth_rate)
    
    if new_children > 0:
        existing_child = db.query(PopulationCohort).filter(
            PopulationCohort.province_id == province_id,
            PopulationCohort.tick_age == 0
        ).first()
        
        if existing_child:
            existing_child.count += new_children
        else:
            child_cohort = PopulationCohort(
                province_id=province_id,
                tick_age=0,
                age_group="kind",
                count=new_children
            )
            db.add(child_cohort)
    
    db.commit()

def get_cohort_count_by_age_group(db: Session, province_id: int, age_group: str) -> int:
    cohorts = db.query(PopulationCohort).filter(
        PopulationCohort.province_id == province_id,
        PopulationCohort.age_group == age_group
    ).all()
    
    return sum(c.count for c in cohorts)

def calculate_bildung(db: Session, province_id: int) -> float:
    cohorts = db.query(PopulationCohort).filter(
        PopulationCohort.province_id == province_id
    ).all()
    
    if not cohorts:
        return 0.0
    
    total_count = sum(c.count for c in cohorts)
    if total_count == 0:
        return 0.0
    
    weighted_age_sum = sum(c.tick_age * c.count for c in cohorts)
    avg_tick_age = weighted_age_sum / total_count
    
    buildings = db.query(BuildingInstance).join(BuildingType).filter(
        BuildingInstance.provinz_id == province_id,
        BuildingType.name.in_(["Schule", "Universität"])
    ).all()
    
    bildungsgebaeude_points = 0
    for building in buildings:
        spec = json.loads(building.type.spezial_eigenschaften or "{}")
        bildungsgebaeude_points += spec.get("bildung", 5) * building.level
    
    bildung = min(100, avg_tick_age * 6 + bildungsgebaeude_points)
    
    return bildung

def calculate_mips_from_workers(db: Session, province_id: int) -> int:
    worker_count = get_cohort_count_by_age_group(db, province_id, "arbeiter")
    
    buildings = db.query(BuildingInstance).join(BuildingType).filter(
        BuildingInstance.provinz_id == province_id,
    ).all()
    
    produktivitaet_modifier = 1.0
    for building in buildings:
        spec = json.loads(building.type.spezial_eigenschaften or "{}")
        produktivitaet_modifier += spec.get("produktivitaet", 0) / 100.0
    
    return int(worker_count * produktivitaet_modifier)

def get_eligible_20_25(db: Session, province_id: int) -> int:
    cohorts = db.query(PopulationCohort).filter(
        PopulationCohort.province_id == province_id,
        PopulationCohort.tick_age.in_([4, 5])
    ).all()
    
    return sum(c.count for c in cohorts)

def update_province_population_stats(db: Session, province_id: int):
    province = db.query(Province).filter(Province.id == province_id).first()
    if not province:
        return
    
    total_population = sum(c.count for c in db.query(PopulationCohort).filter(
        PopulationCohort.province_id == province_id
    ).all())
    
    if total_population > 0:
        province.population = total_population
    else:
        province.population = max(1, province.population)
    
    mips_available = calculate_mips_from_workers(db, province_id)
    if mips_available > 0:
        province.mips = mips_available
    
    db.commit()

def get_population_summary(db: Session, province_id: int) -> dict:
    initialize_population_cohorts(db, province_id)
    
    kind_count = get_cohort_count_by_age_group(db, province_id, "kind")
    arbeiter_count = get_cohort_count_by_age_group(db, province_id, "arbeiter")
    rentner_count = get_cohort_count_by_age_group(db, province_id, "rentner")
    
    total_population = kind_count + arbeiter_count + rentner_count
    
    bildung = calculate_bildung(db, province_id)
    
    eligible_20_25 = get_eligible_20_25(db, province_id)
    
    return {
        "total": total_population,
        "kind": kind_count,
        "arbeiter": arbeiter_count,
        "rentner": rentner_count,
        "eligible_20_25": eligible_20_25,
        "bildung": bildung
    }

def get_population_forecast(db: Session, province_id: int, ticks: int = 5) -> list:
    initialize_population_cohorts(db, province_id)
    
    current_cohorts = []
    for c in db.query(PopulationCohort).filter(
        PopulationCohort.province_id == province_id
    ).all():
        current_cohorts.append({
            "tick_age": c.tick_age,
            "age_group": c.age_group,
            "count": c.count
        })
    
    forecast = []
    
    for t in range(ticks):
        projected_cohorts = []
        
        new_counts = {}
        
        for cohort in current_cohorts:
            new_tick_age = cohort["tick_age"] + 1
            new_age_group = get_age_group(new_tick_age)
            
            death_rate = get_death_rate(new_tick_age)
            if death_rate >= 1.0:
                continue
            
            surviving = int(cohort["count"] * (1 - death_rate))
            
            key = (new_tick_age, new_age_group)
            if key in new_counts:
                new_counts[key] += surviving
            else:
                new_counts[key] = surviving
        
        for (tick_age, age_group), count in new_counts.items():
            projected_cohorts.append({
                "tick_age": tick_age,
                "age_group": age_group,
                "count": count
            })
        
        kind_count = sum(c["count"] for c in projected_cohorts if c["age_group"] == "kind")
        arbeiter_count = sum(c["count"] for c in projected_cohorts if c["age_group"] == "arbeiter")
        rentner_count = sum(c["count"] for c in projected_cohorts if c["age_group"] == "rentner")
        
        forecast.append({
            "tick": t + 1,
            "total": sum(c["count"] for c in projected_cohorts),
            "kind": kind_count,
            "arbeiter": arbeiter_count,
            "rentner": rentner_count
        })
        
        current_cohorts = projected_cohorts
    
    return forecast

def get_soziale_settings(db: Session, province_id: int) -> TaxSettings:
    settings = db.query(TaxSettings).filter(
        TaxSettings.province_id == province_id
    ).first()
    
    if not settings:
        settings = TaxSettings(province_id=province_id)
        db.add(settings)
        db.commit()
    
    return settings

def update_soziale_settings(db: Session, province_id: int, kindergeld_rate: float = None, rente_rate: float = None) -> dict:
    settings = get_soziale_settings(db, province_id)
    
    if kindergeld_rate is not None:
        settings.kindergeld_rate = max(0, kindergeld_rate)
    if rente_rate is not None:
        settings.rente_rate = max(0, rente_rate)
    
    db.commit()
    
    return {
        "kindergeld_rate": settings.kindergeld_rate,
        "rente_rate": settings.rente_rate
    }

def process_kindergeld_and_rente(db: Session, province_id: int):
    from .finance_logic import has_steueramt
    
    if not has_steueramt(db, province_id):
        return {"kindergeld": 0, "rente": 0}
    
    province = db.query(Province).filter(Province.id == province_id).first()
    if not province:
        return {"kindergeld": 0, "rente": 0}
    
    settings = get_soziale_settings(db, province_id)
    
    kindergeld_rate = getattr(settings, 'kindergeld_rate', 0.5)
    rente_rate = settings.rente_rate
    
    kind_count = get_cohort_count_by_age_group(db, province_id, "kind")
    rentner_count = get_cohort_count_by_age_group(db, province_id, "rentner")
    
    kindergeld_total = kind_count * kindergeld_rate
    rente_total = rentner_count * rente_rate
    
    total_payment = kindergeld_total + rente_total
    
    if province.provinzkonto >= total_payment:
        province.provinzkonto -= total_payment
        province.volkskonto += total_payment
        
        return {
            "kindergeld": kindergeld_total,
            "rente": rente_total
        }
    else:
        available = province.provinzkonto
        
        if total_payment > 0:
            kindergeld_ratio = kindergeld_total / total_payment
        else:
            kindergeld_ratio = 0
        
        province.provinzkonto = 0
        province.volkskonto += available
        
        return {
            "kindergeld": available * kindergeld_ratio,
            "rente": available * (1 - kindergeld_ratio)
        }